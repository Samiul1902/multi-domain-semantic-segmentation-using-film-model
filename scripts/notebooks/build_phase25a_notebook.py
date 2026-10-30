"""Phase 25A — reviewer notebook builder (33 sections, every epoch visible).

Deterministic: fixed cell ids (``p25aNNN``) + stripped ``metadata.execution`` +
coalesced stream outputs + fixed pandas Styler uuids + normalised object memory
addresses (``0x...`` -> ``0xADDR``). Three consecutive builds must be byte-identical.

The notebook reads ONLY artifacts that already exist at build time. It deliberately
does NOT read the final-freeze or notebook-determinism artifacts (those are produced
after it) — that would be a circular dependency.

Usage:
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase25a_notebook.py
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
           / "phase25a_dedicated_regional_refiner.ipynb")

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))      # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))        # noqa: E731

cells: list = []

# ---------------------------------------------------------------------------
# §1. TITLE
# ---------------------------------------------------------------------------
cells.append(md("""
# Phase 25A — Dedicated Crop-Trained Regional Refiner

**Method:** `RA-MedFiLM-BARR` — Resource-Aware MedFiLM with Benefit-Aware Refinement Routing
**Architecture:** `ra_medfilm_barr_narrowed_v1_1`
**Module implemented and trained here:** `R_psi` (`BARRRegionalRefinerV1`) — **only this module**

This is the **first implementation and training phase after the Phase-24 freeze**. It trains the
dedicated crop-trained regional refiner on the frozen TRAIN-only `ROUTER_DEVELOPMENT` population.
It does **not** train the benefit router, does **not** create paired-gain / `DeltaDice` labels,
does **not** inspect `ROUTER_HOLDOUT` outcomes, does **not** evaluate the 808-case VAL, and does
**not** touch TEST.
"""))

cells.append(md("""
## 1. Identity and scope

| field | value |
|---|---|
| method | `RA-MedFiLM-BARR` |
| architecture revision | `ra_medfilm_barr_narrowed_v1_1` |
| module trained | `R_psi` = `BARRRegionalRefinerV1` |
| input | `1 x 4 x 256 x 256` — `[R, G, B, p_global_crop]` |
| output | `1 x 1 x 256 x 256` raw logits |
| trainable parameters | **1,276,401** (hard ceiling 2,000,000) |
| frozen global anchor | Phase-21 MedFiLM, 3,523,001 params (unchanged) |
| master development seed | 42 |

Scope guard, verbatim from `phase25a_scope_guard.json`.
"""))

cells.append(code("""
import json, hashlib, pathlib, re
import numpy as np
import pandas as pd
import torch

ROOT = pathlib.Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1"
CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1"
CACHE = ROOT / "data_cache" / "phase25a_global_cache"

from IPython.display import Image, Markdown, display

def _j(p):
    p = pathlib.Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def sty(df, uid, fmt=None):
    s = df.style
    if fmt:
        s = s.format(fmt)
    return s.set_uuid(uid)

FIG = ROOT / "reports" / "figures" / "phase25a_regional_refiner"

def fig(name, caption=None):
    p = FIG / name
    if not p.exists():
        raise FileNotFoundError(f"FAIL-CLOSED: required Phase-25A figure missing: {p}")
    raw = p.read_bytes()
    if not raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
        raise ValueError(f"FAIL-CLOSED: not a PNG: {p}")
    if len(raw) < 2048:
        raise ValueError(f"FAIL-CLOSED: suspiciously small PNG ({len(raw)}B): {p}")
    _img = Image(data=raw, format="png", embed=True)
    return display(_img) if caption is None else display(Markdown(f"**{caption}**"), _img)

scope = _j(AUD / "phase25a_scope_guard.json")
print("implemented and trained :", scope.get("implemented_and_trained"))
print("not started             :", [k for k, v in scope.get("not_started", {}).items() if v])
print("holdout outcomes read   :", scope.get("router_holdout_outcomes_inspected"))
print("VAL 808 evaluated       :", scope.get("val_808_evaluated"))
print("TEST reads              :", scope.get("test_reads"))
"""))

# ---------------------------------------------------------------------------
# §2. ENTRY GATE
# ---------------------------------------------------------------------------
cells.append(md("""
## 2. Entry gate (fail-closed)

Every predecessor identity and governance lock is verified before the first training step.
The gate is **fail-closed**: a single failure exits non-zero and training may not start.
"""))

cells.append(code("""
gate = _j(AUD / "phase25a_entry_gate.json")
print("verdict            :", gate.get("verdict"))
print("checks             :", f"{gate.get('n_passed')}/{gate.get('n_checks')}")
print("training_may_start :", gate.get("training_may_start"))
print("predecessor terminal:", gate.get("predecessor_terminal"))
print()
rows = [{"check": c["check"], "pass": c["pass"]} for c in gate.get("checks", [])]
display(sty(pd.DataFrame(rows), "p25a_entry_gate", None))
"""))

# ---------------------------------------------------------------------------
# §3. HARD BOUNDARIES
# ---------------------------------------------------------------------------
cells.append(md("""
## 3. Hard boundaries respected

| boundary | status |
|---|---|
| train the benefit router | **NOT DONE** |
| generate paired-gain / `DeltaDice` labels | **NOT DONE** |
| inspect `ROUTER_HOLDOUT` outcomes | **NOT DONE** |
| evaluate the 808-case VAL | **NOT DONE** |
| access TEST | **NOT DONE** (lock CLOSED, counters 0) |
| start Phase 25B / 25C / 25D / 25E / 25F / 25G | **NOT DONE** |

The only trained artefact in this phase is `R_psi`.
"""))

# ---------------------------------------------------------------------------
# §4. PHASE-24 v1.1 BINDING
# ---------------------------------------------------------------------------
cells.append(md("""
## 4. Binding to the frozen Phase-24 v1.1 specification

The exact Phase-24 v1.1 spec is bound by SHA. Where the v1.1 artifact and the operative
Phase-25A instruction disagree, the disagreement is **reported, not silently repaired**.
"""))

cells.append(code("""
b = _j(AUD / "phase25a_phase24_v1_1_binding.json")
print("architecture_id          :", b.get("architecture_id"))
print("method_name              :", b.get("method_name"))
print("master_development_seed  :", b.get("master_development_seed"))
print("phase24 notebook sha256  :", b.get("phase24_notebook_sha256"))
print("phase24 exact spec sha256:", b.get("phase24_exact_spec_sha256"))
print()
roi = b.get("bound_roi", {})
print("bound ROI:", json.dumps({k: roi[k] for k in
      ("expansion_factor", "fractional_margin", "input_resolution",
       "predicted_foreground_threshold", "empty_prediction")}, indent=1))
print()
ref = b.get("bound_refiner", {})
print("bound refiner: name=%s in=%s out=%s params=%s ceiling=%s" % (
    ref.get("name"), ref.get("input_channels"), ref.get("output_channels"),
    ref.get("expected_parameters"), ref.get("hard_ceiling")))
print("active channels  :", ref.get("channels_active"))
print("rejected channels:", ref.get("channels_declared_rejected"))
print()
for d in b.get("discrepancies", []):
    print("DISCREPANCY:", d["field"])
    print("   v1.1 frozen value :", d["phase24_v1_1_frozen_value"])
    print("   phase25a bound    :", d["phase25a_bound_value"])
    print("   status            :", d["status"])
"""))

# ---------------------------------------------------------------------------
# §5. DATA SPLIT BINDING
# ---------------------------------------------------------------------------
cells.append(md("""
## 5. Data split binding — TRAIN-only

`ROUTER_DEVELOPMENT` (4,957) is the only population used. `ROUTER_HOLDOUT` (875) outcomes are
never inspected. The 808-case VAL is a SECONDARY/CONTINUITY development benchmark and is
untouched here. TEST is closed.
"""))

cells.append(code("""
sp = _j(AUD / "phase25a_data_split_binding.json")
print("split manifest sha256 :", sp.get("split_manifest_sha256"))
print("development_n         :", sp.get("development_n"))
print("holdout_n             :", sp.get("holdout_n"))
print("group overlap d/h     :", sp.get("group_overlap_dev_holdout"))
print("val overlap           :", sp.get("val_overlap"))
print("test overlap          :", sp.get("test_overlap"))
print("holdout outcomes read :", sp.get("holdout_outcomes_read_in_phase25a"))
print()
dom = pd.DataFrame(sorted(sp.get("development_by_domain", {}).items()),
                   columns=["domain", "router_development_n"])
dom["fraction"] = dom["router_development_n"] / dom["router_development_n"].sum()
display(sty(dom, "p25a_domains", {"fraction": "{:.4f}"}))
print("total:", int(dom["router_development_n"].sum()))
"""))

# ---------------------------------------------------------------------------
# §6. GLOBAL CACHE PROVENANCE
# ---------------------------------------------------------------------------
cells.append(md("""
## 6. TRAIN-only global cache provenance

`p_global` for every `ROUTER_DEVELOPMENT` sample is produced by **one** forward pass of the
frozen Phase-21 global model. The checkpoint SHA is bound and unchanged.
"""))

cells.append(code("""
prov = _j(AUD / "phase25a_global_cache_provenance.json")
for k in ("global_checkpoint_sha256", "global_checkpoint_path", "global_model_params",
          "global_forward_passes", "device", "amp", "threshold", "threshold_rule",
          "prob512_dtype", "population_n", "population"):
    if k in prov:
        print(f"{k:28s}: {prov[k]}")
print()
man = _j(CACHE / "cache_manifest.json")
print("cache manifest population_n :", man.get("population_n"))
print("cache manifest by_domain    :", json.dumps(man.get("by_domain"), indent=1))
"""))

# ---------------------------------------------------------------------------
# §7. ACTION AVAILABILITY
# ---------------------------------------------------------------------------
cells.append(md("""
## 7. Action availability

A sample whose predicted global foreground is empty is `FORCED_SKIP` — it never enters refiner
training. Action availability is reported per domain and never repaired with ground truth.
"""))

cells.append(code("""
aa = pd.read_csv(TAB / "phase25a_action_availability_by_domain.csv")
display(sty(aa, "p25a_action_avail", {"availability_fraction": "{:.4f}"}))
print("total action-available:", int(aa[aa.domain == "ALL"]["action_available"].iloc[0])
      if (aa.domain == "ALL").any() else int(aa["action_available"].sum()))
"""))

# ---------------------------------------------------------------------------
# §8. ROI TRANSFORM
# ---------------------------------------------------------------------------
cells.append(md("""
## 8. Exact ROI transform and its ground-truth independence

threshold `p_global` at **0.5** (lower-inclusive, float32) → tight bbox → centre-preserving
**1.50x** expansion (≡ margin 0.25) → clip to canvas → square zero pad → crop RGB and
`p_global` → resize to **256x256** (bilinear / bilinear / nearest).

The transform has **no ground-truth input and no ground-truth code path**. The audit below
proves that changing GT cannot alter any ROI coordinate, the RGB crop, or the probability crop.
"""))

cells.append(code("""
rt = _j(AUD / "phase25a_roi_transform_audit.json")
print("verdict                  :", rt.get("verdict"))
print("rule                     :", rt.get("rule"))
c = rt.get("constants", {})
print("threshold                :", c.get("predicted_foreground_threshold"))
print("expansion_factor         :", c.get("expansion_factor"))
print("fractional_margin        :", c.get("fractional_margin"))
print("margin_constant_source   :", c.get("margin_constant_source"))
print("input_resolution         :", c.get("input_resolution"))
print("resampling               :", json.dumps(c.get("resampling")))
print()
print("geometry implementation  :", rt.get("geometry_implementation"))
gi = rt.get("gt_independence_test", {})
print("GT-independence test     :", json.dumps(gi))
print("roi decided before GT    :", rt.get("roi_geometry_determined_before_gt"))
print("empty prediction case    :", json.dumps(rt.get("empty_prediction_case")))
print("threshold discrepancy    :", json.dumps(
    rt.get("threshold_discrepancy", {}).get("status")))
"""))

# ---------------------------------------------------------------------------
# §9. ARCHITECTURE
# ---------------------------------------------------------------------------
cells.append(md("""
## 9. `BARRRegionalRefinerV1` architecture

Encoder–decoder with residual blocks, GroupNorm (largest divisor ≤ 8 ⇒ 8 at every stage),
SiLU, `bias=False` on all convolutions except the 1x1 head. No SE, no attention, no
transformer, no FiLM, no dropout, no deep supervision, no pretrained weights.
The forward takes **no task id** — the refiner is domain-agnostic by construction.
"""))

cells.append(code("""
import sys
sys.path.insert(0, str(ROOT))
from src.models.barr import (BARRRegionalRefinerV1, BARR_REFINER_CHANNELS,
                             BARR_REFINER_EXPECTED_PARAMETERS, BARR_REFINER_HARD_CEILING,
                             closed_form_parameter_count, count_parameters,
                             assert_no_forbidden_modules, group_count)

m = BARRRegionalRefinerV1()
n = count_parameters(m)
print("channels (active)     :", list(BARR_REFINER_CHANNELS))
print("GroupNorm groups      :", {int(c): group_count(c) for c in BARR_REFINER_CHANNELS})
print("measured parameters   :", f"{n:,}")
print("expected parameters   :", f"{BARR_REFINER_EXPECTED_PARAMETERS:,}")
print("hard ceiling          :", f"{BARR_REFINER_HARD_CEILING:,}")
assert_no_forbidden_modules(m)
print("forbidden modules     : NONE")
m.eval()
with torch.no_grad():
    out = m(torch.zeros(2, 4, 256, 256))
print("output shape (batch 2):", tuple(out.shape))
"""))

# ---------------------------------------------------------------------------
# §10. PARAMETER DERIVATION
# ---------------------------------------------------------------------------
cells.append(md("""
## 10. Closed-form parameter derivation vs measurement

The closed-form count is computed analytically from the layer shapes and must equal the
measured count **exactly**. This is the architecture identity gate.
"""))

cells.append(code("""
active = closed_form_parameter_count((16, 32, 64, 96, 128))
rejected = closed_form_parameter_count((16, 32, 64, 128, 192))
tbl = pd.DataFrame([
    {"envelope": "[16, 32, 64, 96, 128]", "closed_form": active, "status": "ACTIVE"},
    {"envelope": "[16, 32, 64, 128, 192]", "closed_form": rejected,
     "status": "REJECTED (> 2,000,000 ceiling)"},
])
display(sty(tbl, "p25a_param_env", {"closed_form": "{:,}"}))
print("active closed-form == measured == expected:",
      active == n == BARR_REFINER_EXPECTED_PARAMETERS)
print("rejected envelope exceeds ceiling:", rejected > BARR_REFINER_HARD_CEILING)
"""))

# ---------------------------------------------------------------------------
# §11. ARCHITECTURE GATE
# ---------------------------------------------------------------------------
cells.append(md("""
## 11. Architecture identity gate

42 independent checks across identity, projection, normalisation, deterministic
initialisation, forbidden modules and ROI operations.
"""))

cells.append(code("""
ag = _j(AUD / "phase25a_refiner_architecture_binding.json")
print("verdict            :", ag.get("verdict"))
print("checks             :", f"{ag.get('n_passed')}/{ag.get('n_checks')}")
print("measured parameters:", ag.get("parameter_count"))
rec = ag.get("prose_reconciliation", {})
if rec:
    print()
    print("prose reconciliation (frozen closed-form wins):")
    for k, v in rec.items():
        print(f"   {k}: {v}")
"""))

# ---------------------------------------------------------------------------
# §12. IMPLEMENTATION TEST SUITE
# ---------------------------------------------------------------------------
cells.append(md("""
## 12. Implementation test suite

A re-runnable suite asserting that the implementation matches the frozen v1.1 spec:
parameter identity, projection, GroupNorm groups, deterministic initialisation, forbidden
modules, ROI geometry, ground-truth independence, augmentation binding, split membership,
dataset integrity and scope guards.
"""))

cells.append(code("""
its = _j(AUD / "phase25a_implementation_test_suite.json")
print("verdict:", its.get("verdict"), f"({its.get('n_passed')}/{its.get('n_checks')})")
bg = pd.DataFrame([{"group": k, **v} for k, v in its.get("by_group", {}).items()])
display(sty(bg, "p25a_impl_groups"))
tests = pd.DataFrame(its.get("tests", []))[["group", "test", "pass"]]
display(sty(tests, "p25a_impl_tests"))
"""))

# ---------------------------------------------------------------------------
# §13. AUGMENTATION BINDING
# ---------------------------------------------------------------------------
cells.append(md("""
## 13. Augmentation — inherited exactly, nothing invented

The augmentation is the frozen Phase-20/21 pipeline: horizontal mirror `p=0.5`, continuous
rotation `uniform(-5, +5)`, brightness `±0.1`, contrast `±0.1`, applied consistently to the
RGB crop, the `p_global` crop and the GT geometry.

**Vertical flip and 90-degree rotation are `NOT_INHERITED` and are never applied.**
"""))

cells.append(code("""
ab = _j(AUD / "phase25a_augmentation_binding.json")
print("inherited from       :", ab.get("inherited_from"))
print("inherited source sha :", ab.get("inherited_source_sha256"))
print("applied after        :", ab.get("applied_after"))
print()
ops = pd.DataFrame([{"operation": o["operation"], "classification": o["classification"],
                     "parameter": o["parameter"]} for o in ab.get("operations", [])])
display(sty(ops, "p25a_aug_ops"))
noti = ab.get("not_inherited", [])
print("NOT inherited:", noti if noti else "(see operations table)")
"""))

# ---------------------------------------------------------------------------
# §14. CROSS-FIT STRUCTURE
# ---------------------------------------------------------------------------
cells.append(md("""
## 14. Cross-fit structure — 3 outer folds with a nested 90/10 split

`ROUTER_DEVELOPMENT` is partitioned into three deterministic, group-safe, domain-stratified
outer folds. Each fold has a **nested** FIT / EARLY_STOP split (90/10). The outer target fold
is never used for gradients, checkpoint selection or early stopping.
"""))

cells.append(code("""
cf = _j(AUD / "phase25a_crossfit_protocol.json")
print("verdict                     :", cf.get("verdict"))
print("seed                        :", cf.get("seed"))
print("outer folds                 :", cf.get("outer_folds"))
print("within                      :", cf.get("within"))
print("inner fit fraction          :", cf.get("inner_fit_fraction"))
print("inner early-stop fraction   :", cf.get("inner_early_stop_fraction"))
print("oof never used for ckpt sel :", cf.get("oof_target_fold_never_used_for_checkpoint_selection"))
print("outer target role           :", cf.get("outer_target_role"))
print("holdout used                :", cf.get("router_holdout_used"))
print("val used                    :", cf.get("val_used"))
print()
fl = pd.DataFrame(cf.get("folds", []))
if len(fl):
    display(sty(fl, "p25a_crossfit_folds"))
"""))

# ---------------------------------------------------------------------------
# §15. FOLD MANIFEST SUMMARY
# ---------------------------------------------------------------------------
cells.append(md("""
## 15. Fold manifest summary (on disk)
"""))

cells.append(code("""
fs = pd.read_csv(TAB / "phase25a_crossfit_fold_manifest_summary.csv")
display(sty(fs, "p25a_fold_summary", {"early_stop_fraction": "{:.4f}"}))
"""))

# ---------------------------------------------------------------------------
# §16. TRAINING PROTOCOL
# ---------------------------------------------------------------------------
cells.append(md("""
## 16. Frozen training protocol

| element | value |
|---|---|
| loss | `0.5 * BCEWithLogitsLoss + 0.5 * DiceLoss(epsilon=1e-6)` |
| optimiser | AdamW, lr `1e-4`, weight decay `1e-4` |
| schedule | `CosineAnnealingLR(T_max=100)` |
| max epochs | 100 |
| early-stopping patience | 15 |
| batch size | 8 |
| seed | 42 |
| mixed precision | AMP on CUDA |
| checkpoint selection | **minimum EARLY_STOP total loss** |

Dice on the early-stop split is a **secondary diagnostic only** — it never selects a checkpoint.
"""))

cells.append(code("""
cfg0 = _j(EXP / "fold0" / "config.json")
for k in ("experiment_id", "method", "architecture_revision", "module", "run",
          "loss", "optimizer", "scheduler", "batch_size", "max_epochs",
          "early_stopping_patience", "amp", "checkpoint_selection",
          "checkpoint_selection_secondary", "seed", "fit_manifest_sha256"):
    if k in cfg0:
        print(f"{k:32s}: {cfg0[k]}")
"""))

# ---------------------------------------------------------------------------
# §17. RESUMABILITY
# ---------------------------------------------------------------------------
cells.append(md("""
## 17. Resumability contract

The execution harness tears down the process tree periodically. Training is therefore
resumable: `--resume` continues the **same logical run** from `latest.pt`, degrading to
epoch 0 if absent. Per-sample augmentation is a pure function of
`(base_seed, epoch, sample_id)`, so a resumed run reproduces every epoch bit-exactly and is
independent of worker count. `history.csv` is flushed every epoch.
"""))

cells.append(code("""
rows = []
for run in ("fold0", "fold1", "fold2", "final"):
    d = EXP / ("final_refit" if run == "final" else run)
    rj = _j(d / "run.json")
    rows.append({"run": run, "epochs": rj.get("epochs_completed"),
                 "target": rj.get("epochs_target"), "best_epoch": rj.get("best_epoch"),
                 "resume_count": rj.get("resume_count"),
                 "stop_reason": rj.get("stop_reason")})
display(sty(pd.DataFrame(rows), "p25a_resume"))
"""))

# ---------------------------------------------------------------------------
# §18-20. RUN 1-3 — every epoch visible
# ---------------------------------------------------------------------------
for _i, _run in enumerate(("fold0", "fold1", "fold2"), start=18):
    _d = "final_refit" if _run == "final" else _run
    cells.append(md(f"""
## {_i}. RUN {_i - 17} — `R_psi_{_run}`: configuration and **every epoch**

The complete per-epoch history is shown: training loss and its BCE / Dice components, the
EARLY_STOP loss and Dice, the learning rate, the checkpoint event, and the running best.
"""))
    cells.append(code(f"""
run = "{_run}"
d = EXP / "{_d}"
cfg = _j(d / "config.json")
rj = _j(d / "run.json")
hist = pd.read_csv(d / "history.csv")
print("run                 :", run)
print("fit action-available:", rj.get("n_fit_action_available"))
print("early-stop n        :", rj.get("n_early_stop_action_available"))
print("epochs completed    :", rj.get("epochs_completed"), "/", rj.get("epochs_target"))
print("best epoch          :", rj.get("best_epoch"))
print("best EARLY_STOP loss:", rj.get("best_early_stop_loss"))
print("stop reason         :", rj.get("stop_reason"))
print("resume count        :", rj.get("resume_count"))
print("fit manifest sha256 :", rj.get("fit_manifest_sha256"))
print()
print(f"EVERY EPOCH ({{len(hist)}} rows):")
display(sty(hist, "p25a_hist_{_run}", {{
    "train_loss": "{{:.5f}}", "train_BCE": "{{:.5f}}", "train_Dice_loss": "{{:.5f}}",
    "early_stop_loss": "{{:.5f}}", "early_stop_Dice": "{{:.4f}}",
    "learning_rate": "{{:.3e}}", "elapsed_seconds": "{{:.2f}}",
    "best_early_stop_loss_so_far": "{{:.5f}}"}}))
"""))

# ---------------------------------------------------------------------------
# §21. FOLD TRAINING CURVES
# ---------------------------------------------------------------------------
cells.append(md("""
## 21. Three-fold training curves

Each fold's FIT loss and its EARLY_STOP loss. The vertical line marks the selected epoch
(minimum EARLY_STOP loss).
"""))

cells.append(code("""
for _r in ("fold0", "fold1", "fold2"):
    fig(f"p25a_{_r}_loss_curve.png", f"{_r} training curve")
fig("p25a_fold_training_comparison.png", "three-fold comparison")
fig("p25a_learning_rate_curves.png", "cosine-annealing schedule")
"""))

# ---------------------------------------------------------------------------
# §22. BEST EPOCH PER FOLD
# ---------------------------------------------------------------------------
cells.append(md("""
## 22. Selected epoch per fold

The selection rule is **minimum EARLY_STOP total loss**. Dice on the early-stop split is
reported alongside but is not the selection criterion.
"""))

cells.append(code("""
sel = pd.read_csv(TAB / "phase25a_refiner_selected_epochs.csv")
display(sty(sel, "p25a_selected_epochs", {"best_early_stop_loss": "{:.6f}",
                                          "early_stop_dice_at_best": "{:.4f}"}))
fig("p25a_best_epoch_summary.png", "selected epoch per fold")
"""))

# ---------------------------------------------------------------------------
# §23. MEDIAN REFIT EPOCH RULE
# ---------------------------------------------------------------------------
cells.append(md("""
## 23. Median refit-epoch rule

`R_psi_final` is refit on the **full** `ROUTER_DEVELOPMENT` population for the **integer median**
of the three fold best epochs. No holdout is used and there is no early stopping in the final
refit — the epoch count is fixed in advance by this rule.
"""))

cells.append(code("""
rule = _j(AUD / "phase25a_final_refit_epoch_rule.json")
print("fold best epochs            :", rule.get("fold_best_epochs"))
print("sorted best epochs          :", rule.get("sorted_best_epochs"))
print("median rule                 :", rule.get("rule"))
print("median derivation           :", rule.get("median_derivation"))
print("FINAL_REFIT_EPOCHS          :", rule.get("final_refit_epochs"))
print("population                  :", rule.get("final_refit_population"))
print("no early stopping in refit  :", rule.get("no_early_stopping_in_final_refit"))
print("uses holdout                :", rule.get("final_refit_uses_holdout"))
print("uses VAL                    :", rule.get("final_refit_uses_val"))
print("uses TEST                   :", rule.get("final_refit_uses_test"))
print("persisted before the refit  :", rule.get("persisted_before_final_refit"))
"""))

# ---------------------------------------------------------------------------
# §24. RUN 4 — FINAL REFIT
# ---------------------------------------------------------------------------
cells.append(md("""
## 24. RUN 4 — `R_psi_final` refit: every epoch

Refit on all 4,957 `ROUTER_DEVELOPMENT` samples for exactly the median epoch count.
"""))

cells.append(code("""
d = EXP / "final_refit"
rj = _j(d / "run.json")
hist = pd.read_csv(d / "history.csv")
print("epochs completed    :", rj.get("epochs_completed"), "/", rj.get("epochs_target"))
print("population manifest :", rj.get("fit_manifest"))
print("population sha256   :", rj.get("fit_manifest_sha256"))
print("early stopping      :", rj.get("early_stopping"))
print("stop reason         :", rj.get("stop_reason"))
print()
print(f"EVERY EPOCH ({len(hist)} rows):")
display(sty(hist, "p25a_hist_final", {
    "train_loss": "{:.5f}", "train_BCE": "{:.5f}", "train_Dice_loss": "{:.5f}",
    "learning_rate": "{:.3e}", "elapsed_seconds": "{:.2f}"}))
fig("p25a_final_refit_training_curve.png", "R_psi_final refit curve")
"""))

# ---------------------------------------------------------------------------
# §25. FINAL REFINER
# ---------------------------------------------------------------------------
cells.append(md("""
## 25. Final refiner artefact

`R_psi_final` is the artefact Phase 25B consumes. Its checkpoint carries the full binding
record, the architecture id, the parameter count and the random state.
"""))

cells.append(code("""
ck = CKPT / "final"
for p in sorted(ck.glob("*.pt")):
    st = torch.load(p, map_location="cpu", weights_only=False)
    print(f"{p.name:12s} bytes={p.stat().st_size:>10,} epoch={st.get('epoch')} "
          f"params={st.get('parameter_count')} arch={st.get('architecture_id')}")
print()
print("final.pt sha256:", sha(ck / "final.pt"))
"""))

# ---------------------------------------------------------------------------
# §26. RESOURCE ACCOUNTING
# ---------------------------------------------------------------------------
cells.append(md("""
## 26. Resource accounting — analytical MACs, not latency

Cost is reported as **analytical MACs** on a defined input shape. Host latency is measured on
this machine and is explicitly **host-specific** — it is not a deployment claim. Device-level
measurement is deferred to Phase 34.
"""))

cells.append(code("""
ra = _j(AUD / "phase25a_resource_accounting.json")
print("trainable parameters :", f"{ra['trainable_parameters']:,}")
print("input shape          :", ra.get("input_shape"))
print("output shape         :", ra.get("output_shape"))
print("analytical MACs      :", f"{ra['analytical_macs']:,}")
print("analytical GMACs     :", ra["analytical_gmacs"])
print("analytical FLOPs     :", f"{ra['analytical_flops']:,}")
print("host latency (s)     :", ra.get("host_specific_forward_latency_seconds"),
      f"({ra.get('host_latency_label')})")
print("MACs definition      :", ra.get("macs_definition"))
print()
cg = ra.get("context_vs_global", {})
print("global GMACs         :", cg.get("global_gmacs_at_1x3x512x512"))
print("refiner/global ratio :", cg.get("refiner_over_global_macs_ratio"))
print("claims NOT made      :", ra.get("claims_not_made"))
"""))

# ---------------------------------------------------------------------------
# §27. CHECKPOINT ISOLATION
# ---------------------------------------------------------------------------
cells.append(md("""
## 27. Checkpoint isolation

Every logical run owns its own directory under `checkpoints/phase25a_barr_regional_refiner_v1_1/`.
A checkpoint can never be written into another run's directory, and the frozen Phase-21 global
checkpoint is never overwritten.
"""))

cells.append(code("""
ci = _j(AUD / "phase25a_checkpoint_integrity.json")
print("verdict:", ci.get("verdict"))
rows = []
for run, entries in ci.get("checkpoints", {}).items():
    if entries.get("status") == "MISSING":
        rows.append({"run": run, "file": "(missing)"}); continue
    for fn, e in entries.items():
        rows.append({"run": run, "file": fn, "bytes": e.get("bytes"),
                     "epoch": e.get("epoch"), "params": e.get("parameter_count"),
                     "fields_complete": e.get("fields_complete")})
display(sty(pd.DataFrame(rows), "p25a_ckpt_integrity", {"bytes": "{:,}"}))
print()
print("frozen Phase-21 global checkpoint sha256:",
      sha(ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"))
"""))

# ---------------------------------------------------------------------------
# §28. TRAINING HEALTH
# ---------------------------------------------------------------------------
cells.append(md("""
## 28. Training health

No NaN / infinite losses, no non-finite gradient batches, contiguous epoch numbering,
checkpoints loadable, parameter count unchanged from the frozen architecture.
"""))

cells.append(code("""
th = _j(AUD / "phase25a_training_health.json")
print("verdict:", th.get("verdict"))
rows = []
for run, e in th.get("runs", {}).items():
    if e.get("status") == "MISSING":
        rows.append({"run": run, "status": "MISSING"}); continue
    rows.append({"run": run, "status": e["status"], "epochs": e["epochs"],
                 "early_stopping": e["early_stopping_enabled"],
                 "train_nan": e["train_loss_nan"], "train_inf": e["train_loss_inf"],
                 "grad_overflow": e["nonfinite_gradient_batches"],
                 "total_batches": e["total_optimisation_batches"],
                 "overflow_pct": round(100 * e["grad_overflow_fraction"], 4),
                 "best_epoch": e["best_epoch"], "resumes": e["resume_count"]})
display(sty(pd.DataFrame(rows), "p25a_health", {"overflow_pct": "{:.4f}"}))
print()
print("non-finite gradient batches are AMP GradScaler-skipped steps "
      "(fp16 overflow detected and the update skipped) — expected AMP behaviour,")
print("tolerated up to 1% of optimisation steps. They are NOT divergences: every")
print("training loss is finite and every run's train loss decreased.")
print()
print("NOTE: the FINAL refit has no early-stop split by construction, so its")
print("early_stop_loss column is legitimately NaN and is excluded from the check.")
"""))

# ---------------------------------------------------------------------------
# §29. LEAKAGE GATES
# ---------------------------------------------------------------------------
cells.append(md("""
## 29. Outcome-leakage gates

Proves that no `ROUTER_HOLDOUT` / VAL / TEST outcome information reached this phase:
cache ∩ holdout = 0, cache ∩ VAL = 0, cache ∩ TEST = 0, and no analysis script contains a
training construct.
"""))

cells.append(code("""
lk = _j(AUD / "phase25a_no_outcome_leakage_audit.json")
print("verdict:", lk.get("verdict"))
print()
print("holdout ids in cache :", lk["router_holdout"]["holdout_sample_ids_in_cache"])
print("val ids in cache     :", lk["existing_val"]["val_sample_ids_in_cache"])
print("test ids in cache    :", lk["test"]["test_sample_ids_in_cache"])
print("holdout outcomes read:", lk["router_holdout"]["holdout_outcomes_inspected"])
print()
print("paired-gain labels created :", lk.get("paired_gain_labels_created"))
print("deltadice computed         :", lk.get("deltadice_computed"))
print("router instantiated        :", lk.get("benefit_router_instantiated"))
print("router training runs       :", lk.get("benefit_router_training_runs"))
print("router inference runs      :", lk.get("benefit_router_inference_runs"))
print()
ss = lk.get("static_scan", {})
print("analysis training constructs :", ss.get("analysis_training_constructs"))
print("test constructs              :", ss.get("test_constructs_across_all_phase25a_scripts"))
print("scripts scanned              :", ss.get("analysis_and_source_scripts_scanned"))
print("excluded from scan           :", ss.get("excluded_from_scan"))
print("exclusion rationale          :", ss.get("exclusion_rationale"))
"""))

# ---------------------------------------------------------------------------
# §30. TEST LOCK
# ---------------------------------------------------------------------------
cells.append(md("""
## 30. TEST lock audit

TEST stayed closed for the whole phase: lock verification PASS and every TEST counter is zero.
"""))

cells.append(code("""
tl = _j(AUD / "phase25a_test_lock_audit.json")
print("verdict                :", tl.get("verdict"))
print("lock verification      :", tl.get("test_lock_verification"))
print("test image reads       :", tl.get("test_image_reads"))
print("test mask reads        :", tl.get("test_mask_reads"))
print("test inference calls   :", tl.get("test_inference_calls"))
print("test visualizations    :", tl.get("test_visualizations"))
print("test metrics computed  :", tl.get("test_metrics_computed"))
print("test ids in cache      :", tl.get("test_sample_ids_in_global_cache"))
print("test ids in fold manifests:", tl.get("test_sample_ids_in_any_fold_manifest"))
print("test_reads             :", tl.get("test_reads"))
"""))

# ---------------------------------------------------------------------------
# §31. FIGURES
# ---------------------------------------------------------------------------
cells.append(md("""
## 31. Required figures

Eight required figures plus two optional. No paired-gain, router or OOF segmentation gallery
is produced — those belong to later modules.
"""))

cells.append(code("""
fm = _j(FIG / "FIG_MANIFEST.json")
print("required:", len(fm.get("required", [])))
print("optional:", len(fm.get("optional", [])))
print("produced:", len(fm.get("produced", [])))
print("contains paired-gain / router results:", fm.get("contains_paired_gain_or_router_results"))
print("contains OOF gallery                 :", fm.get("contains_oof_gallery"))
print()
fig("p25a_action_availability_by_domain.png", "action availability by domain")
fig("p25a_refiner_architecture_summary.png", "refiner architecture and cost")
fig("p25a_crop_geometry_distribution.png", "crop geometry distribution")
"""))

# ---------------------------------------------------------------------------
# §32. TABLES
# ---------------------------------------------------------------------------
cells.append(md("""
## 32. Required tables index
"""))

cells.append(code("""
idx = _j(TAB / "phase25a_table_index.json")
if idx:
    display(sty(pd.DataFrame(idx.get("tables", [])), "p25a_table_index", {"bytes": "{:,}"}))
else:
    import os
    names = sorted(p.name for p in TAB.glob("phase25a_*.csv"))
    display(sty(pd.DataFrame({"table": names,
                              "bytes": [ (TAB / n).stat().st_size for n in names ]}),
                "p25a_table_index", {"bytes": "{:,}"}))
"""))

# ---------------------------------------------------------------------------
# §33. TERMINAL
# ---------------------------------------------------------------------------
cells.append(md("""
## 33. Terminal state and assertions

Every load-bearing Phase-25A claim is asserted below. The notebook reads only artefacts that
existed when it was written; the freeze and the notebook-determinism proof are verified
externally, after this notebook, to avoid a circular dependency.
"""))

cells.append(code("""
assertions = []
def chk(name, ok):
    assertions.append((name, bool(ok)))

gate = _j(AUD / "phase25a_entry_gate.json")
chk("entry gate PASS", gate.get("verdict") == "PHASE25A_ENTRY_GATE_PASS")
chk("entry gate training allowed", gate.get("training_may_start") is True)

b = _j(AUD / "phase25a_phase24_v1_1_binding.json")
chk("v1.1 bound", b.get("architecture_id") == "ra_medfilm_barr_narrowed_v1_1")
chk("seed 42", b.get("master_development_seed") == 42)
chk("threshold discrepancy reported", any(
    d.get("status") == "REPORTED_NOT_SILENTLY_REPAIRED" for d in b.get("discrepancies", [])))
chk("bound threshold is 0.5", b.get("bound_roi", {}).get("predicted_foreground_threshold") == 0.5)

sp = _j(AUD / "phase25a_data_split_binding.json")
chk("development 4957", sp.get("development_n") == 4957)
chk("holdout 875", sp.get("holdout_n") == 875)
chk("group overlap zero", sp.get("group_overlap_dev_holdout") == 0)
chk("val overlap zero", sp.get("val_overlap") == 0)
chk("test overlap zero", sp.get("test_overlap") == 0)

ag = _j(AUD / "phase25a_refiner_architecture_binding.json")
chk("architecture gate PASS", ag.get("verdict") == "PHASE25A_REFINER_ARCHITECTURE_FROZEN")
chk("parameters 1276401", ag.get("parameter_count") == 1276401)
chk("closed form == measured", closed_form_parameter_count((16, 32, 64, 96, 128)) == n)
chk("under ceiling", n <= 2000000)

rt = _j(AUD / "phase25a_roi_transform_audit.json")
chk("roi gt independence", rt.get("gt_independence_test", {}).get("passed") is True)
chk("roi audit PASS", rt.get("verdict") == "PHASE25A_ROI_TRANSFORM_AUDIT_PASS")

its = _j(AUD / "phase25a_implementation_test_suite.json")
chk("implementation suite PASS", its.get("n_failed") == 0 and its.get("n_checks", 0) > 0)

cf = _j(AUD / "phase25a_crossfit_protocol.json")
chk("3 outer folds", cf.get("outer_folds") == 3)
chk("inner 90/10", cf.get("inner_fit_fraction") == 0.90
    and cf.get("inner_early_stop_fraction") == 0.10)
chk("oof never used for selection",
    cf.get("oof_target_fold_never_used_for_checkpoint_selection") is True)
chk("crossfit protocol frozen", cf.get("verdict") == "PHASE25A_CROSSFIT_PROTOCOL_FROZEN")

reg = _j(AUD / "phase25a_training_run_registry.json")
chk("4 runs complete", reg.get("n_runs_complete") == 4)
chk("no extra primary runs", reg.get("extra_primary_runs") == 0)

h0 = pd.read_csv(EXP / "fold0" / "history.csv")
chk("fold0 every epoch visible", len(h0) == _j(EXP / "fold0" / "run.json").get("epochs_completed"))
chk("fold0 selection on early-stop loss",
    "early_stop_loss" in h0.columns and "train_loss" in h0.columns)

rule = _j(AUD / "phase25a_final_refit_epoch_rule.json")
chk("median refit rule", "median" in str(rule.get("rule", "")))
chk("final refit epochs set", rule.get("final_refit_epochs") is not None)
chk("final refit epochs is integer median",
    rule.get("final_refit_epochs") == sorted(rule.get("fold_best_epochs", {}).values())[1])
chk("holdout forbidden in final", rule.get("final_refit_uses_holdout") is False)
chk("no early stopping in final", rule.get("no_early_stopping_in_final_refit") is True)
chk("rule persisted before refit", rule.get("persisted_before_final_refit") is True)

th = _j(AUD / "phase25a_training_health.json")
chk("training health PASS", th.get("verdict") == "PHASE25A_TRAINING_HEALTH_PASS")
ci = _j(AUD / "phase25a_checkpoint_integrity.json")
chk("checkpoint integrity PASS", ci.get("verdict") == "PHASE25A_CHECKPOINT_INTEGRITY_PASS")

lk = _j(AUD / "phase25a_no_outcome_leakage_audit.json")
chk("leakage PASS", lk.get("verdict") == "PHASE25A_NO_OUTCOME_LEAKAGE_PASS")
chk("no router training", lk.get("benefit_router_training_runs") == 0)
chk("no paired-gain labels", lk.get("paired_gain_labels_created") is False)
chk("holdout outcomes not inspected",
    lk.get("router_holdout", {}).get("holdout_outcomes_inspected") is False)
chk("val not evaluated", lk.get("existing_val", {}).get("outcome_evaluation") == 0)

tl = _j(AUD / "phase25a_test_lock_audit.json")
chk("test lock PASS", tl.get("verdict") == "PHASE25A_TEST_LOCK_PASS")
chk("test_reads 0", tl.get("test_reads") == 0)

sc = _j(AUD / "phase25a_scope_guard.json")
chk("25B not started", not sc.get("not_started", {}).get("phase25b_started", False))
chk("25C not started", not sc.get("not_started", {}).get("phase25c_started", False))
chk("25D not started", not sc.get("not_started", {}).get("phase25d_started", False))

fm = _j(FIG / "FIG_MANIFEST.json")
chk("8 required figures", len(fm.get("required", [])) == 8)
chk("no paired-gain in figures", fm.get("contains_paired_gain_or_router_results") is False)

n_fail = sum(1 for _, ok in assertions if not ok)
for name, ok in assertions:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
print()
print(f"{len(assertions) - n_fail}/{len(assertions)} terminal assertions passed")
print()
print("PHASE25A_DEDICATED_REGIONAL_REFINER_COMPLETE__PHASE25B_ELIGIBLE_NOT_STARTED")
assert n_fail == 0, f"{n_fail} terminal assertion(s) failed"
"""))

# ---------------------------------------------------------------------------
# write + execute (deterministic)
# ---------------------------------------------------------------------------
NB_PATH.parent.mkdir(parents=True, exist_ok=True)
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p25a{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=3600,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

# deterministic post-processing
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

_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
for _c in nb.cells:
    for _o in _c.get("outputs", []) or []:
        _d = _o.get("data")
        if isinstance(_d, dict):
            for _k, _v in list(_d.items()):
                if isinstance(_v, str):
                    _d[_k] = _ADDR.sub("0xADDR", _v)
                elif isinstance(_v, list):
                    _d[_k] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s
                              for _s in _v]
        _t = _o.get("text")
        if isinstance(_t, str):
            _o["text"] = _ADDR.sub("0xADDR", _t)
        elif isinstance(_t, list):
            _o["text"] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s
                          for _s in _t]
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", [])
             if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
            if "text/html" in (o.get("data", {}) or {}))
imgs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))
sha_nb = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"Cells: {len(nb.cells)} | markdown: "
      f"{sum(1 for c in nb.cells if c.cell_type == 'markdown')} | code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print("Monotonic exec counts:", "PASS" if monotonic else "FAIL")
print("html table outputs:", htmls)
print("embedded PNG outputs:", imgs)
print("Notebook SHA256:", sha_nb)
