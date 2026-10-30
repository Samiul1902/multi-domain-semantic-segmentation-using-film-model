"""Phase 21 — build the Global MedFiLM reviewer notebook (full scientific evidence).

Determinism: deterministic cell ids + stripped ``metadata.execution`` + coalesced
stream outputs + fixed pandas Styler uuids (``set_uuid``) + normalised object
memory addresses (``0x...`` -> ``0xADDR``). Three consecutive builds must be
byte-identical.

The notebook runs NO training and NO inference. Every number, table and figure is
rebuilt from persisted artifacts.

Usage
-----
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase21_notebook.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_DIR = ROOT / "notebooks/phasewise/phase_21_global_medfilm"
NB_PATH = NB_DIR / "phase21_global_medfilm_reference.ipynb"
NB_DIR.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))          # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))            # noqa: E731

cells: list = []

# 01 ----------------------------------------------------------------------- #
cells.append(md("""
# Phase 21 — Global MedFiLM Reference
### Four-domain task-conditioned global segmentation · full reviewer evidence

| Item | Value |
|---|---|
| Phase | 21 (Stage B) |
| Canonical folder | `notebooks/phasewise/phase_21_global_medfilm/` |
| Model | **ONE** shared four-domain task-conditioned Global MedFiLM |
| Task conditioning | FiLM `F_hat = (1 + gamma(t)) * F + beta(t)` at 5 sites |
| Shared output | ONE 1x1 head -> single foreground logit (no dataset-specific head) |
| Protocol | inherited EXACTLY from `reports/audits/phase20_shared_global_baseline_protocol.json` |
| Manifest | `manifests/phase4_v3` (TRAIN 5832 / VAL 808) |
| Selection rule | `phase20_macro_domain_mean_dice_v1` (frozen) |
| Cohorts read | TRAIN and VAL only |
| TEST | **CLOSED** — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Canonical VAL inference runs | exactly **1** |
| Logical training runs | exactly **1** (no architecture sweep, no hyperparameter sweep) |
| Terminal state | `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED` |

**Scope guard.** Phase 21 is a **GLOBAL reference only**. It is **NOT** the final
RA-MedFiLM-Seg++ model. It contains NO ROI proposal, NO localizer, NO regional refiner,
NO high-resolution crop branch, NO global-regional fusion, NO benefit predictor, NO
counterfactual refinement gain, NO resource/budget router, NO adaptive conditional
computation, NO compression/pruning/quantization/distillation, NO architecture search,
and NO TEST evaluation.

**Interpretation guard.** There is **no architecture-matched control** (no identical plain
model trained under this Phase-21 run). The only permitted phrasing is
*"Global MedFiLM achieved X compared with baseline Y"*. Claiming *"FiLM caused +X"* is
**forbidden**. Where a paired CI overlaps zero, the models are **not separable**.
"""))

# 02 ----------------------------------------------------------------------- #
cells.append(md("## 1. Environment and deterministic setup"))
cells.append(code("""
import sys, json, hashlib, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

ROOT = Path(r"D:/Softfors/jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from IPython.display import display, Markdown, Image

from src.analysis import phase21_figures as F

EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
AUD, TAB = ROOT / "reports/audits", ROOT / "reports/tables"
FIG = ROOT / "reports/figures/phase21_global_medfilm"

def load(name):
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

def sty(df, uid, fmt=None, **kw):
    \"\"\"Deterministic Styler (fixed uuid => SHA-stable notebook output).\"\"\"
    fmt = {**(fmt or {}), **kw}
    return df.style.format(fmt).set_uuid(uid)

print("numpy", np.__version__, "| pandas", pd.__version__)
"""))

# 03 ----------------------------------------------------------------------- #
cells.append(md("## 2. Governance and TEST lock"))
cells.append(code("""
from src.utils.test_lock import verify_test_lock
verify_test_lock(str(ROOT))

FREEZE = load("phase21_final_freeze.json")
# The final freeze is written AFTER the notebook in the canonical pipeline order.
# When the freeze is absent (e.g. a pre-freeze notebook build), fall back to the
# same static interpretation guard so the notebook stays buildable and does NOT
# weaken the guard; once the freeze exists it is authoritative.
INTERP_FALLBACK = {
    "permitted": "Global MedFiLM achieved X compared with baseline Y.",
    "forbidden": "FiLM caused +X.",
    "reason": ("No architecture-matched control exists (no identical plain model trained "
               "under the Phase-21 run), so the difference cannot be causally attributed to FiLM."),
}
FREEZE.setdefault("interpretation", INTERP_FALLBACK)
gov = FREEZE.get("governance", {})
display(sty(pd.DataFrame([
    {"check": "TEST image reads", "value": gov.get("test_locks", {}).get("test_image_reads")},
    {"check": "TEST mask reads", "value": gov.get("test_locks", {}).get("test_mask_reads")},
    {"check": "TEST inference", "value": gov.get("test_locks", {}).get("test_inference")},
    {"check": "TEST visualizations", "value": gov.get("test_locks", {}).get("test_visualization")},
    {"check": "TEST reads observed (all artifacts)", "value": gov.get("test_reads_total_observed")},
    {"check": "FiLM used", "value": gov.get("film_used")},
    {"check": "Task conditioning used", "value": gov.get("task_conditioning_used")},
    {"check": "Forbidden components present", "value": gov.get("forbidden_components_present")},
]), "p21_gov", value="{!s}"))
print("TEST lock verified against manifests/test.csv sha256.")
"""))

# 04 ----------------------------------------------------------------------- #
cells.append(md("## 3. Data contract and populations"))
cells.append(code("""
EG = load("phase21_entry_gate.json")
display(sty(pd.DataFrame([
    {"item": "manifest_version", "value": EG.get("manifest_version")},
    {"item": "TRAIN population", "value": EG.get("train_population")},
    {"item": "VAL population", "value": EG.get("val_population")},
    {"item": "Task IDs", "value": json.dumps(EG.get("task_ids"))},
    {"item": "Entry-gate verdict", "value": EG.get("verdict")},
    {"item": "Entry-gate checks passed", "value": f"{EG.get('n_passed')}/{EG.get('n_checks')}"},
]), "p21_data", value="{!s}"))

run = pd.read_csv(ROOT / "experiments" / EXP / "history.csv")
print(f"Training history rows: {len(run)}")
"""))

# 05 ----------------------------------------------------------------------- #
cells.append(md("## 4. Task-ID registry and conditioning policy"))
cells.append(code("""
PB = load("phase21_protocol_binding.json")
task = PB.get("inherited_values", {}).get("task_ids", {})
display(sty(pd.DataFrame([
    {"task_id": 0, "domain": "ISIC", "modality": "dermoscopy (RGB)", "role": "FiLM conditioning"},
    {"task_id": 1, "domain": "BUSI", "modality": "ultrasound (L)", "role": "FiLM conditioning"},
    {"task_id": 2, "domain": "KVASIR", "modality": "endoscopy (RGB)", "role": "FiLM conditioning"},
    {"task_id": 3, "domain": "KUB", "modality": "radiograph (L/RGB)", "role": "FiLM conditioning"},
]), "p21_tasks", value="{!s}"))
print("task_id is CONDITIONING_ALLOWED but is NEVER a channel, never concatenated to the image,")
print("and never selects a dataset-specific head. Kidney/Ureteric/Bladder and TINY/SMALL/")
print("MEDIUM/LARGE are NEVER model inputs.")
"""))

# 06 ----------------------------------------------------------------------- #
cells.append(md("## 5. Protocol binding — Phase-20 inheritance"))
cells.append(code("""
inv = PB.get("inherited_values", {})
rows = [{"field": k, "phase20": json.dumps(v["phase20_protocol_value"])[:60],
         "phase21": json.dumps(v["phase21_value"])[:60], "identical": v["identical"]}
        for k, v in inv.items()]
display(sty(pd.DataFrame(rows), "p21_proto"))
print("Inherited identical:", PB.get("n_inherited_identical"), "/", PB.get("n_inherited_checks"))
print("Unintentional differences:", PB.get("unintentional_differences"))
print("Verdict:", PB.get("verdict"))
display(sty(pd.DataFrame(PB.get("intentional_differences", []))[
    ["field", "class", "reason"]], "p21_intent"))
"""))

# 07 ----------------------------------------------------------------------- #
cells.append(md("## 6. Legacy MedFiLM architecture audit"))
cells.append(code("""
LA = load("phase21_legacy_medfilm_architecture_audit.json")
display(sty(pd.DataFrame([
    {"item": "evidence status", "value": LA.get("evidence_status")},
    {"item": "historical result claimed as current", "value": LA.get("not_current_prospective_result") is False},
    {"item": "legacy model class", "value": LA.get("historical_class_names", {}).get("film_model")},
    {"item": "FiLM module class", "value": LA.get("historical_class_names", {}).get("film_module")},
    {"item": "FiLM equation", "value": LA.get("film_equation", {}).get("form")},
    {"item": "FiLM sites", "value": json.dumps(LA.get("film_insertion_locations", {}).get("order"))},
    {"item": "squeeze-excitation", "value": LA.get("topology_features", {}).get("squeeze_excitation")},
    {"item": "deep supervision", "value": LA.get("topology_features", {}).get("deep_supervision")},
    {"item": "legacy task count", "value": LA.get("four_domain_compatibility", {}).get("legacy_task_count")},
    {"item": "legacy hyperparameters adopted", "value": False},
]), "p21_legacy", value="{!s}"))
"""))

# 08 ----------------------------------------------------------------------- #
cells.append(md("## 7. Frozen architecture definition"))
cells.append(code("""
AB = load("phase21_global_medfilm_architecture_binding.json")
spec = AB.get("component_specification", {})
display(sty(pd.DataFrame([
    {"item": "architecture_id", "value": AB.get("architecture_id")},
    {"item": "verdict", "value": AB.get("verdict")},
    {"item": "frozen before training", "value": AB.get("frozen_before_training")},
    {"item": "measured parameters", "value": AB.get("measured_parameter_count")},
    {"item": "one shared parameter set", "value": AB.get("one_shared_parameter_set")},
    {"item": "dataset-specific head", "value": AB.get("dataset_specific_head")},
    {"item": "output definition", "value": AB.get("output_definition")},
    {"item": "forbidden-module audit passed", "value": AB.get("forbidden_module_audit", {}).get("passed")},
]), "p21_arch", value="{!s}"))
display(sty(pd.DataFrame(
    [{"component": k, "present": v} for k, v in spec.get("present", {}).items()]
    + [{"component": k, "present": v} for k, v in spec.get("absent", {}).items()]), "p21_arch2"))
"""))

# 09 ----------------------------------------------------------------------- #
cells.append(md("## 8. FiLM mechanism"))
cells.append(code("""
tc = AB.get("component_specification", {}).get("task_conditioning", {})
display(sty(pd.DataFrame([{"property": k, "value": json.dumps(v) if not isinstance(v, str) else v}
                          for k, v in tc.items()]), "p21_film_spec"))
print("Identity at initialisation: the FiLM output projection is zero-initialised, so every")
print("site starts as F_hat = F exactly. Task conditioning is therefore LEARNED, not injected.")
"""))

# 10 ----------------------------------------------------------------------- #
cells.append(md("## 9. Pre-execution checks"))
cells.append(code("""
PE = load("phase21_pre_execution_check.json")
rows = [{"check": k, "passed": v["passed"], "detail": json.dumps(v["detail"])[:90]}
        for k, v in PE.get("checks", {}).items()]
display(sty(pd.DataFrame(rows), "p21_pec"))
print("Verdict:", PE.get("verdict"), "|", PE.get("n_passed"), "/", PE.get("n_checks"),
      "| training_may_start:", PE.get("training_may_start"))
"""))

# 11 ----------------------------------------------------------------------- #
cells.append(md("## 10. Training configuration (inherited protocol)"))
cells.append(code("""
cfg = json.loads((ROOT / "experiments" / EXP / "config.json").read_text(encoding="utf-8"))
display(sty(pd.DataFrame([
    {"field": "loss", "value": json.dumps(cfg["loss"])},
    {"field": "optimizer", "value": json.dumps(cfg["optimizer"])},
    {"field": "scheduler", "value": json.dumps(cfg["scheduler"])},
    {"field": "batch_size", "value": cfg["training"]["batch_size"]},
    {"field": "eval_batch_size", "value": cfg["training"]["eval_batch_size"]},
    {"field": "amp", "value": cfg["training"]["amp"]},
    {"field": "seed", "value": cfg["training"]["seed"]},
    {"field": "max_epochs", "value": cfg["training"]["max_epochs"]},
    {"field": "early_stopping_patience", "value": cfg["training"]["early_stopping_patience"]},
    {"field": "sampling_policy", "value": cfg["training"]["sampling_policy"]},
    {"field": "checkpoint_metric", "value": cfg["training"]["checkpoint_metric"]},
    {"field": "input_channel_policy", "value": cfg["input_channel_policy"]},
    {"field": "input_resolution", "value": cfg["input_resolution"]},
]), "p21_cfg", value="{!s}"))
"""))

# 12 ----------------------------------------------------------------------- #
cells.append(md("## 11. Training run manifest"))
cells.append(code("""
RM = json.loads((ROOT / "experiments" / EXP / "run_manifest.json").read_text(encoding="utf-8"))
display(sty(pd.DataFrame([
    {"item": "experiment_id", "value": RM["experiment_id"]},
    {"item": "architecture_id", "value": RM["architecture_id"]},
    {"item": "model params", "value": RM["model_params"]},
    {"item": "TRAIN total", "value": RM["dataset_populations"]["TRAIN_total"]},
    {"item": "VAL total", "value": RM["dataset_populations"]["VAL_total"]},
    {"item": "torch", "value": RM["environment"]["torch"]},
    {"item": "gpu", "value": RM["environment"]["gpu_name"]},
    {"item": "run started (UTC)", "value": RM["run_started_utc"]},
]), "p21_rm", value="{!s}"))
display(sty(pd.DataFrame([{"code": k, "sha256": v[:16] + "..."}
                          for k, v in RM["code_shas"].items()]), "p21_rm2"))
"""))

# 13 ----------------------------------------------------------------------- #
cells.append(md("## 12. Training curves — loss"))
cells.append(code("""
CACHE = F.build_all(progress=lambda *a, **k: None)
INV_OUT = F.write_inventories()

# Embedding-size policy (empirically calibrated from the corrupted package).
#
# MEASURED FACT: in the previous reviewer package the corrupted ``image/png``
# payloads were exactly the largest ones. Their base64 lengths were
# 1,346,139 / 1,270,209 / 701,719 characters, and all three came back with an
# ODD length (i.e. exactly one character lost) while still ending in a valid PNG
# ``IEND`` terminator. Corruption was probabilistic above ~7e5 chars: the
# 1,635,252 / 1,528,600 / 864,064-char payloads survived by luck.
#
# MEASURED SIZE GAP in the frozen inventory: the 8 multi-panel gallery figures
# are 544,836-1,635,252 base64 chars, while ALL 35 non-gallery figures are
# <= 85,876 chars. A single blanket cap would therefore silently DOWNSCALE the
# 35 small figures (which never needed it) and degrade reviewer figure quality.
#
# Policy: preserve FULL SOURCE RESOLUTION whenever the payload is inside the
# measured-safe envelope, and downscale only the oversized gallery panels.
FIG_EMBED_SAFE_B64 = 250_000         # safely above 85,876, far below 544,836
FIG_EMBED_MAX_PX = 1600              # never exceed the source panel width

def _bounded_png(path):
    \"\"\"Return PNG bytes for `path` at full fidelity when it fits the safe envelope.

    Returns ``(data, (w, h))``. Figures whose base64 payload is already within
    ``FIG_EMBED_SAFE_B64`` are returned BYTE-IDENTICAL to the source file, so no
    reviewer-visible detail is lost. Only oversized payloads (the multi-panel
    galleries) are progressively downscaled until they fit.
    \"\"\"
    import base64, io
    from PIL import Image as _PILImage

    raw = open(path, "rb").read()
    if len(base64.b64encode(raw)) <= FIG_EMBED_SAFE_B64:
        with _PILImage.open(io.BytesIO(raw)) as _im:
            return raw, (_im.width, _im.height)      # full source fidelity

    with _PILImage.open(path) as im:
        im = im.convert("RGB") if im.mode not in ("RGB", "L") else im.copy()
        scale = 1.0
        while True:
            w = max(1, int(round(im.width * scale)))
            h = max(1, int(round(im.height * scale)))
            if max(w, h) > FIG_EMBED_MAX_PX:
                scale *= 0.9
                continue
            buf = io.BytesIO()
            im.resize((w, h), _PILImage.LANCZOS).save(buf, format="PNG",
                                                      optimize=True)
            data = buf.getvalue()
            if len(base64.b64encode(data)) <= FIG_EMBED_SAFE_B64 or scale < 0.2:
                return data, (w, h)
            scale *= 0.85

def show_fig(fig_id, width=1050):
    \"\"\"Embed one inventory figure EXACTLY ONCE, from the frozen inventory.

    The payload is embedded at FULL SOURCE RESOLUTION whenever it fits the
    measured-safe base64 envelope; only the oversized gallery panels are
    downscaled (see ``_bounded_png``). Identifier resolution is driven by
    ``phase21_figure_inventory.csv`` so a figure can never be silently skipped
    by a hardcoded list.
    \"\"\"
    import base64 as _b64
    inv = F.figure_inventory()
    row = inv[inv["figure_id"] == fig_id]
    assert len(row) == 1, f"missing figure: {fig_id}"
    rel = str(row.iloc[0]["saved_path"])
    display(Markdown(f"*Figure — {row.iloc[0]['title']}*  \\n`{rel}`"))
    p = ROOT / rel
    assert p.exists(), f"figure file absent on disk: {p}"
    data, (w, h) = _bounded_png(p)
    b64 = _b64.b64encode(data).decode("ascii")
    assert len(b64) % 4 == 0, f"base64 length not a multiple of 4 for {fig_id}"
    # NOTE: pass the base64 string through ``Image(data=...)`` only when it is a
    # list of chunks; a bare ``str`` is interpreted by IPython as a FILE PATH.
    # The robust route is to hand ``display`` the raw PNG bytes via Image(data=...)
    # with an explicit ``format='png'`` and ``embed=True``.
    display(Image(data=data, format="png", embed=True, width=min(width, w)))

def show_group(prefix, width=900):
    \"\"\"Embed every inventory figure whose id starts with `prefix`.\"\"\"
    ids = sorted(fid for fid in F.figure_inventory()["figure_id"]
                 if str(fid).startswith(prefix))
    print(f"{prefix}* : {len(ids)} figure(s) in the frozen inventory")
    for fid in ids:
        show_fig(fid, width=width)
    return ids

show_fig("p21_train_loss")
show_fig("p21_train_epoch_time")
"""))

# 14 ----------------------------------------------------------------------- #
cells.append(md("## 13. Training curves — macro Dice and frozen selection"))
cells.append(code("""
show_fig("p21_train_macro")
best_ep = int(run.loc[run["macro_domain_dice"].idxmax(), "epoch"])
display(sty(pd.DataFrame([
    {"item": "best epoch (in-loop)", "value": best_ep},
    {"item": "best macro-domain Dice", "value": float(run["macro_domain_dice"].max())},
    {"item": "final epoch", "value": int(run["epoch"].iloc[-1])},
]), "p21_best", value="{!s}"))
"""))

# 15 ----------------------------------------------------------------------- #
cells.append(md("## 14. Training curves — per-domain Dice"))
cells.append(code("""
show_fig("p21_train_domain_dice")
cols = ["epoch", "train_loss", "val_loss", "macro_domain_dice"] + [f"val_dice_{d}" for d in ["ISIC","BUSI","KVASIR","KUB"]]
display(sty(run[cols].tail(12), "p21_tail"))
"""))

# 16 ----------------------------------------------------------------------- #
cells.append(md("## 15. Learning-rate schedule and early stopping"))
cells.append(code("""
show_fig("p21_train_lr")
show_fig("p21_train_earlystop")
"""))

# 17 ----------------------------------------------------------------------- #
cells.append(md("## 16. Checkpoint selection replay (disk only)"))
cells.append(code("""
RP = json.loads((ROOT / "experiments" / EXP /
                 "phase21_checkpoint_selection_replay.json").read_text(encoding="utf-8"))
display(sty(pd.DataFrame([
    {"item": "selection rule", "value": RP["selection_rule_id"]},
    {"item": "replayed best epoch", "value": RP["replayed_best_epoch"]},
    {"item": "replayed macro Dice", "value": RP["replayed_best_macro_domain_dice"]},
    {"item": "training best epoch", "value": RP["training_best_epoch"]},
    {"item": "matches training", "value": RP["replay_matches_training"]},
    {"item": "verdict", "value": RP["verdict"]},
]), "p21_replay", value="{!s}"))
"""))

# 18 ----------------------------------------------------------------------- #
cells.append(md("## 17. Training closure"))
cells.append(code("""
CL = json.loads((ROOT / "experiments" / EXP /
                 "phase21_training_closure.json").read_text(encoding="utf-8"))
display(sty(pd.DataFrame([
    {"item": "best epoch", "value": CL["best_epoch"]},
    {"item": "best macro-domain Dice", "value": CL["best_macro_domain_dice"]},
    {"item": "best val loss", "value": CL["best_val_loss"]},
    {"item": "final epoch", "value": CL["final_epoch"]},
    {"item": "stop reason", "value": CL["stop_reason"]},
    {"item": "resume count", "value": CL["resume_count"]},
    {"item": "independent duplicate runs", "value": CL["independent_duplicate_runs"]},
    {"item": "model params", "value": CL["model_params"]},
    {"item": "elapsed (h)", "value": round(CL["total_elapsed_seconds"]/3600, 2)},
    {"item": "checkpoint replay verdict", "value": CL["checkpoint_selection_replay_verdict"]},
]), "p21_closure", value="{!s}"))
display(sty(pd.DataFrame([{"domain": k, "dice_at_best": v}
                          for k, v in CL["per_domain_dice_at_best"].items()]), "p21_closure2"))
"""))

# 19 ----------------------------------------------------------------------- #
cells.append(md("## 18. Canonical VAL evaluation"))
cells.append(code("""
VE = load("phase21_val_evaluation.json")
PM = load("phase21_prediction_manifest.json")
display(sty(pd.DataFrame([
    {"item": "canonical VAL inference runs", "value": VE["canonical_val_inference_runs"]},
    {"item": "samples expected", "value": VE["samples_expected"]},
    {"item": "samples evaluated", "value": VE["samples_evaluated"]},
    {"item": "threshold", "value": VE["threshold"]},
    {"item": "no TTA", "value": VE["no_tta"]},
    {"item": "no threshold tuning", "value": VE["no_threshold_tuning"]},
    {"item": "no morphology", "value": VE["no_morphology"]},
    {"item": "prob maps persisted", "value": VE["prob_maps_persisted"]},
    {"item": "checkpoint SHA (16)", "value": VE["checkpoint_sha256"][:16] + "..."},
]), "p21_val", value="{!s}"))
display(sty(pd.DataFrame([{"domain": k, "n": v}
                          for k, v in PM["per_domain_counts"].items()]), "p21_val2"))
"""))

# 20 ----------------------------------------------------------------------- #
cells.append(md("## 19. Per-domain performance"))
cells.append(code("""
DP = pd.read_csv(TAB / "phase21_global_medfilm_domain_performance.csv")
cols = ["row_type", "dataset", "n", "dice", "dice_ci_low", "dice_ci_high", "iou",
        "precision", "recall", "specificity", "balanced_accuracy", "mcc",
        "hd95", "assd", "surface_dice", "roc_auc", "pr_auc", "brier", "ece", "mce"]
display(sty(DP[cols], "p21_dp"))
"""))

# 21 ----------------------------------------------------------------------- #
cells.append(md("## 20. Macro-domain result and 95% CI"))
cells.append(code("""
AN = load("phase21_analysis.json")
gm = AN["global_medfilm"]
display(sty(pd.DataFrame([
    {"item": "macro-domain VAL Dice", "value": gm["macro_domain_dice"]},
    {"item": "95% CI low", "value": gm["macro_domain_dice_ci_low"]},
    {"item": "95% CI high", "value": gm["macro_domain_dice_ci_high"]},
    {"item": "macro-domain IoU", "value": gm["macro_domain_iou"]},
    {"item": "pooled Dice (descriptive)", "value": gm["pooled_dice_descriptive"]},
    {"item": "rank among six models", "value": f"{gm['rank_among_six']}/6"},
]), "p21_macro", value="{!s}"))
display(sty(pd.DataFrame([{"domain": k, "dice": v}
                          for k, v in gm["per_domain_dice"].items()]), "p21_macro2"))
"""))

# 22 ----------------------------------------------------------------------- #
cells.append(md("## 21. Confusion matrices"))
cells.append(code("""
show_fig("p21_confusion")
CM = pd.read_csv(TAB / "phase21_global_medfilm_confusion_matrices.csv")
display(sty(CM[["scope", "tp", "tn", "fp", "fn", "total", "row_norm_gt_fg_tp",
                "row_norm_gt_fg_fn", "row_norm_gt_bg_fp", "row_norm_gt_bg_tn"]], "p21_cm"))
"""))

# 23 ----------------------------------------------------------------------- #
cells.append(md("## 22. Calibration and ranking metrics"))
cells.append(code("""
show_fig("p21_ranking")
show_fig("p21_calibration")
display(sty(pd.read_csv(TAB / "phase21_global_medfilm_calibration_ranking.csv"), "p21_cal"))
"""))

# 24 ----------------------------------------------------------------------- #
cells.append(md("## 23. Six-model benchmark comparison"))
cells.append(code("""
show_fig("p21_cmp_macro")
CMP = pd.read_csv(TAB / "phase21_six_model_comparison.csv")
display(sty(CMP[["model_key", "display_name", "phase", "params", "macro_domain_dice",
                 "macro_domain_dice_ci_low", "macro_domain_dice_ci_high",
                 "dice_ISIC", "dice_BUSI", "dice_KVASIR", "dice_KUB"]], "p21_cmp"))
show_fig("p21_cmp_params")
"""))

# 25 ----------------------------------------------------------------------- #
cells.append(md("""
## 24. Per-domain matrix across six models

Every metric matrix present in the frozen figure inventory is embedded below. The
set is read from `phase21_figure_inventory.csv` rather than hardcoded, so a metric
cannot be silently omitted from the reviewer package again.
"""))
cells.append(code("""
show_fig("p21_cmp_domain_matrix")
# Drive coverage from the FROZEN INVENTORY, not from a hardcoded list: the old
# five-item loop silently dropped specificity / mcc / balanced_accuracy / assd /
# surface_dice from the reviewer package.
_metric_ids = sorted(
    fid for fid in F.figure_inventory()["figure_id"]
    if str(fid).startswith("p21_metric_"))
print(f"metric-matrix figures in the frozen inventory: {len(_metric_ids)}")
for _fid in _metric_ids:
    show_fig(_fid, width=820)
"""))

# 26 ----------------------------------------------------------------------- #
cells.append(md("## 25. Paired domain-stratified bootstrap vs the five frozen baselines"))
cells.append(code("""
show_fig("p21_cmp_paired")
PA = pd.read_csv(TAB / "phase21_paired_bootstrap_vs_baselines.csv")
display(sty(PA[["model_b", "observed_diff", "diff_ci_low", "diff_ci_high",
                "ci_excludes_zero", "p_value_two_sided", "significant_at_0.05"]], "p21_pa"))
PBJ = load("phase21_paired_bootstrap.json")
print("n_boot:", PBJ["n_boot"], "| seed:", PBJ["seed"], "| unit:", PBJ["resampling_unit"])
"""))

# 27 ----------------------------------------------------------------------- #
cells.append(md("## 26. Statistical interpretation guard"))
cells.append(code("""
sig = AN["paired_bootstrap"]["significant_vs_baselines"]
ns = AN["paired_bootstrap"]["non_significant_vs_baselines"]
print("PERMITTED :", FREEZE["interpretation"]["permitted"])
print("FORBIDDEN :", FREEZE["interpretation"]["forbidden"])
print("Reason    :", FREEZE["interpretation"]["reason"])
print()
print("Differences that are statistically separable (CI excludes 0):", sig)
print("Differences whose CI OVERLAPS zero (models NOT separable)     :", ns)
print()
print("No causal attribution to FiLM is made anywhere in this package.")
"""))

# 28 ----------------------------------------------------------------------- #
cells.append(md("## 27. KUB subgroup analysis (REPORTING ONLY)"))
cells.append(code("""
show_fig("p21_kub_subgroup")
KS = pd.read_csv(TAB / "phase21_kub_subgroup_analysis.csv")
display(sty(KS, "p21_ks"))
print("Kidney/Ureteric/Bladder categories are REPORTING-ONLY and are NEVER model inputs.")
"""))

# 29 ----------------------------------------------------------------------- #
cells.append(md("## 28. KUB size stratification (TINY preserved for Phase 22)"))
cells.append(code("""
show_fig("p21_kub_size")
KZ = pd.read_csv(TAB / "phase21_kub_size_stratification.csv")
display(sty(KZ, "p21_kz"))
print("Taxonomy: kub_size_clean_v3_v1 (FROZEN). TINY stratum is preserved as evidence and was")
print("NOT optimised on.")
"""))

# 30 ----------------------------------------------------------------------- #
cells.append(md("## 29. Task-conditioning diagnostic"))
cells.append(code("""
show_fig("p21_conditioning")
CD = load("phase21_task_conditioning_diagnostic.json")
display(sty(pd.DataFrame([
    {"item": "scope", "value": CD["scope"]},
    {"item": "n cases", "value": CD["n_cases"]},
    {"item": "mean |delta Dice| with wrong task", "value": CD["mean_abs_delta_dice_wrong_task"]},
    {"item": "max |delta Dice| with wrong task", "value": CD["max_abs_delta_dice_wrong_task"]},
    {"item": "mean Dice with correct task", "value": CD["mean_dice_correct_task"]},
    {"item": "flag", "value": CD["flag"]},
    {"item": "flag rule", "value": CD["flag_rule"]},
]), "p21_cd", value="{!s}"))
display(Markdown(f"> {CD['honesty_note']}"))
display(sty(pd.read_csv(TAB / "phase21_task_conditioning_diagnostic.csv"), "p21_cd2"))
"""))

# 31 ----------------------------------------------------------------------- #
cells.append(md("## 30. FiLM parameter sanity"))
cells.append(code("""
show_fig("p21_film_gamma_mean_abs")
show_fig("p21_film_beta_mean_abs")
show_fig("p21_film_gamma_l2_norm")
show_fig("p21_film_beta_l2_norm")
FS = pd.read_csv(TAB / "phase21_film_parameter_summary.csv")
display(sty(FS.head(20), "p21_fs"))
print("gamma = tanh(gamma_raw), beta = tanh(beta_raw) => |gamma|,|beta| < 1 by construction.")
"""))

# 32 ----------------------------------------------------------------------- #
cells.append(md("## 31. Gallery — frozen 64 cases, six-model panel"))
cells.append(code("""
G = pd.read_csv(TAB / "phase21_gallery_selection_64.csv")
display(sty(G.groupby("dataset").size().reset_index(name="n"), "p21_g"))
show_group("p21_gallery_six_", width=1050)
print("The frozen 64-case gallery (16 per domain) was reused UNCHANGED across all six models.")
"""))

# 33 ----------------------------------------------------------------------- #
cells.append(md("## 32. Detailed gallery (ANALYTICAL_OUTCOME_SELECTED)"))
cells.append(code("""
show_group("p21_detailed_gallery_", width=1000)
print("These panels are explicitly labelled ANALYTICAL_OUTCOME_SELECTED and are DISTINCT from")
print("the fixed 64-case gallery above.")
"""))

# 34 ----------------------------------------------------------------------- #
cells.append(md("## 33. Failure analysis"))
cells.append(code("""
show_fig("p21_failure_worst16", width=1000)
show_fig("p21_failure_dist")
PI = pd.read_csv(TAB / "phase21_per_image_val_metrics.csv")
display(sty(PI.groupby("dataset").agg(n=("dice", "size"), mean_dice=("dice", "mean"),
                                      min_dice=("dice", "min"),
                                      p10_dice=("dice", lambda s: s.quantile(0.10)),
                                      empty_pred=("pred_empty", "sum")).reset_index(), "p21_fail"))
"""))

# 35 ----------------------------------------------------------------------- #
cells.append(md("## 34. Parameter and compute accounting (measurement only)"))
cells.append(code("""
# Drive EVERY efficiency figure from the frozen inventory so none can be dropped.
_eff_ids = sorted(
    fid for fid in F.figure_inventory()["figure_id"]
    if str(fid).startswith("p21_eff_"))
print(f"efficiency figures in the frozen inventory: {len(_eff_ids)}")
for _fid in _eff_ids:
    show_fig(_fid, width=900)
EF = pd.read_csv(TAB / "phase21_efficiency_accounting.csv")
display(sty(EF, "p21_ef"))
"""))

# 36 ----------------------------------------------------------------------- #
cells.append(md("""
## 35. Lightweight future-design note (additive roadmap — NOT solved here)

Phase 21 does **not** solve lightweight deployment. This note is an **additive roadmap** only.

- The Global MedFiLM reference has **3,523,001** parameters and one shared head, which is
  already far smaller than the 40.3 M DeepLabV3+ baseline; parameter count is therefore not
  the binding constraint identified by this phase.
- The measured bottleneck remains **KUB tiny objects**, not model size.
- Any future lightweight work (distillation, pruning, quantization, mobile export) belongs to a
  later phase and must be evaluated under its own frozen protocol with its own controls.
- **No** compression, pruning, quantization, distillation or architecture search was performed
  in Phase 21, and none of those results are claimed here.
"""))

# 37 ----------------------------------------------------------------------- #
cells.append(md("## 36. Figures inventory and visualization coverage"))
cells.append(code("""
INV = pd.read_csv(FIG / "phase21_figure_inventory.csv")
display(sty(pd.DataFrame([
    {"item": "figures", "value": len(INV)},
    {"item": "embedded in notebook", "value": int(INV["embedded_in_notebook"].sum())},
    {"item": "groups", "value": json.dumps(INV.groupby("group").size().to_dict())},
]), "p21_inv", value="{!s}"))
display(sty(INV.groupby(["group", "category"]).size().reset_index(name="n"), "p21_inv2"))
"""))

# 38 ----------------------------------------------------------------------- #
cells.append(md("## 37. Artifact index"))
cells.append(code("""
# The artifact index lists the STABLE evidence this notebook summarises. The two
# self-referential finalisation artifacts are excluded by design: the notebook
# embeds phase21_final_freeze.json's own SHA/size, and the freeze records the
# notebook SHA, so including either would make the notebook permanently
# non-byte-identical across rebuilds.
SELF_REFERENTIAL = {"phase21_final_freeze.json", "phase21_notebook_determinism.json"}
rows = []
for f in sorted((AUD).glob("phase21_*.json")):
    if f.name in SELF_REFERENTIAL:
        continue
    rows.append({"artifact": f.name, "sha256": sha(f)[:16] + "...",
                 "bytes": f.stat().st_size})
display(sty(pd.DataFrame(rows), "p21_art"))
rows = []
for f in sorted((TAB).glob("phase21_*.csv")):
    rows.append({"table": f.name, "sha256": sha(f)[:16] + "...", "bytes": f.stat().st_size})
display(sty(pd.DataFrame(rows), "p21_tab"))
"""))

# 39 ----------------------------------------------------------------------- #
cells.append(md("## 38. Terminal state and Phase-22 eligibility"))
cells.append(code("""
print("terminal_state   :", FREEZE.get("terminal_state"))
print("phase22_eligible :", FREEZE.get("phase22_eligible"))
print("phase22_started  :", FREEZE.get("phase22_started"))
print("freeze_verified  :", FREEZE.get("freeze_verified"))
print("validation_problems:", FREEZE.get("validation_problems"))
# The final terminal state is only asserted once the freeze is VERIFIED. During the
# bootstrap build the freeze is intentionally incomplete (the 3-build notebook
# determinism proof cannot exist yet), so asserting it here would be circular.
# Phase 22 must never be started regardless of freeze status.
assert FREEZE.get("phase22_started", False) is False
if FREEZE.get("freeze_verified") is True:
    assert FREEZE["terminal_state"] == "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED"
    print()
    print("Phase 21 is COMPLETE. Phase 22 is ELIGIBLE but NOT STARTED.")
else:
    print()
    print("FREEZE NOT YET VERIFIED (status:", FREEZE.get("terminal_state"), ")")
    print("This is expected on the bootstrap build: the freeze records "
          "'notebook determinism not proven' until the 3-build proof completes.")
    print("The terminal-state assertion is re-checked on the post-freeze builds, "
          "and the freeze writer fails closed unless the state is "
          "PHASE22_ELIGIBLE_NOT_STARTED.")
"""))

# 40 ----------------------------------------------------------------------- #
cells.append(md("""
## 39. Reproduction

```bash
# 1. pre-training governance (fail-closed)
./.venv/Scripts/python.exe scripts/audits/phase21_entry_gate.py
./.venv/Scripts/python.exe scripts/audits/write_phase21_legacy_audit.py
./.venv/Scripts/python.exe scripts/audits/write_phase21_protocol_binding.py
./.venv/Scripts/python.exe scripts/audits/write_phase21_architecture_binding.py
./.venv/Scripts/python.exe scripts/audits/write_phase21_pre_execution_check.py

# 2. the ONE authorized training run (resumable; never a second logical run)
./.venv/Scripts/python.exe -u scripts/training/train_phase21_global_medfilm.py --resume

# 3. ONE canonical VAL pass
./.venv/Scripts/python.exe scripts/evaluation/evaluate_phase21_val.py

# 4. analysis / diagnostics / accounting
./.venv/Scripts/python.exe scripts/analysis/run_phase21_analysis.py
./.venv/Scripts/python.exe scripts/analysis/phase21_conditioning_diagnostic.py
./.venv/Scripts/python.exe scripts/analysis/phase21_efficiency.py

# 5. figures + freeze
./.venv/Scripts/python.exe -c "from src.analysis import phase21_figures as F; F.build_all(); F.write_inventories()"
./.venv/Scripts/python.exe scripts/analysis/write_phase21_freeze.py
```

**TEST is never read at any step.**
"""))

# write + execute ------------------------------------------------------------ #
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p21{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=7200,
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
# Binary image payloads MUST NEVER be rewritten. A base64 payload can contain a
# literal "0x" followed by >=6 hex characters; substituting "0xADDR" changes the
# string length, destroys the base64 padding, and yields exactly the corruption
# signature seen in the original package ("Excess data after padding" and
# impossible non-multiple-of-4 lengths). This was the true root cause of the
# reviewer-notebook defect.
_BINARY_KEYS = {"image/png", "image/jpeg", "image/gif", "image/bmp",
                "application/pdf"}
for _c in nb.cells:
    for _o in _c.get("outputs", []) or []:
        _d = _o.get("data")
        if isinstance(_d, dict):
            for _k, _v in list(_d.items()):
                if _k in _BINARY_KEYS:
                    continue
                if isinstance(_v, str):
                    _d[_k] = _ADDR.sub("0xADDR", _v)
                elif isinstance(_v, list):
                    _d[_k] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s for _s in _v]
        _t = _o.get("text")
        if isinstance(_t, str):
            _o["text"] = _ADDR.sub("0xADDR", _t)
        elif isinstance(_t, list):
            _o["text"] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s for _s in _t]
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
pngs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))
htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
            if "text/html" in (o.get("data", {}) or {}))
sha_nb = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"Cells: {len(nb.cells)} | markdown: {sum(1 for c in nb.cells if c.cell_type=='markdown')} "
      f"| code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print("Monotonic exec counts (1..%d): %s" % (len(code_cells), "PASS" if monotonic else "FAIL"))
print(f"image/png outputs: {pngs} | html table outputs: {htmls}")
print("Notebook SHA:", sha_nb)
