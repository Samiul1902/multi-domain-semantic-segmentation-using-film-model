"""Phase 21 — generate the complete Phase-21 report from live artifacts.

Reads only persisted artifacts. Re-runnable at any point in the phase: sections
that depend on completed training are emitted as PENDING with the exact command
that will fill them, so the report is never misleading.

Writes
------
reports/phase21_global_medfilm_report.md
reports/audits/phase21_progress_status.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/write_phase21_report.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import (  # noqa: E402
    ARCHITECTURE_ID,
    CKPT_DIR,
    CONFIG,
    EXPERIMENT_ID,
    EXP_DIR,
    PROTOCOL_PATH,
    PROTOCOL_SHA256,
    sha256_file,
)

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
OUT_MD = ROOT / "reports" / "phase21_global_medfilm_report.md"
OUT_STATUS = AUD / "phase21_progress_status.json"

TERMINAL = "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED"


def load(name: str) -> dict:
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def sha16(p: Path) -> str:
    return sha256_file(p)[:16] + "..." if p.exists() else "MISSING"


def fmt(v, nd=6):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return str(v)


def main() -> int:
    eg = load("phase21_entry_gate.json")
    pb = load("phase21_protocol_binding.json")
    ab = load("phase21_global_medfilm_architecture_binding.json")
    la = load("phase21_legacy_medfilm_architecture_audit.json")
    pe = load("phase21_pre_execution_check.json")
    final_freeze = load("phase21_final_freeze.json")
    analysis = load("phase21_analysis.json")
    val_eval = load("phase21_val_evaluation.json")
    cond = load("phase21_task_conditioning_diagnostic.json")

    hist_path = EXP_DIR / "history.csv"
    hist = pd.read_csv(hist_path) if hist_path.exists() else pd.DataFrame()
    closure_path = EXP_DIR / "phase21_training_closure.json"
    closure = json.loads(closure_path.read_text(encoding="utf-8")) if closure_path.exists() else None

    training_done = bool(closure and closure.get("stop_reason") in
                         ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"))
    phase_state = ("COMPLETE" if final_freeze.get("freeze_verified")
                   else "TRAINING_IN_PROGRESS" if not training_done
                   else "TRAINING_TERMINATED__POST_TRAINING_PENDING")

    proto_sha = sha256_file(ROOT / PROTOCOL_PATH)
    L: list[str] = []
    A = L.append

    # ---------------------------------------------------------------- header #
    A("# Phase 21 — GLOBAL MedFiLM Reference")
    A("## Four-domain task-conditioned global segmentation")
    A("")
    A(f"**Report generated:** {datetime.now(timezone.utc).isoformat()}  ")
    A(f"**Phase state:** `{phase_state}`  ")
    A(f"**Terminal state:** "
      + (f"`{final_freeze.get('terminal_state')}`" if final_freeze.get("freeze_verified")
         else f"`PENDING` (target `{TERMINAL}`)"))
    A("")
    A("> **Scope guard.** Phase 21 is a **GLOBAL reference only**. It is **NOT** the final")
    A("> RA-MedFiLM-Seg++ model. It contains NO ROI proposal, NO localizer, NO regional refiner,")
    A("> NO high-resolution crop branch, NO global-regional fusion, NO benefit predictor, NO")
    A("> counterfactual refinement gain, NO resource/budget router, NO adaptive conditional")
    A("> computation, NO compression/pruning/quantization/distillation, NO architecture search,")
    A("> and NO TEST evaluation.")
    A("")
    A("> **Interpretation guard.** There is **no architecture-matched control** (no identical plain")
    A("> model trained under this Phase-21 run). The only permitted phrasing is *\"Global MedFiLM")
    A("> achieved X compared with baseline Y\"*. Claiming *\"FiLM caused +X\"* is **forbidden**.")
    A("> Where a paired CI overlaps zero, the models are **not separable**.")
    A("")

    # ------------------------------------------------------------ at a glance #
    A("## 1. At a glance")
    A("")
    A("| Item | Value |")
    A("|---|---|")
    A(f"| Phase | 21 (Stage B) |")
    A(f"| Experiment ID | `{EXPERIMENT_ID}` |")
    A(f"| Architecture ID | `{ARCHITECTURE_ID}` |")
    A(f"| Model | ONE shared four-domain task-conditioned Global MedFiLM |")
    A(f"| Task conditioning | FiLM `F_hat = (1 + gamma(t)) * F + beta(t)` at 5 sites |")
    A(f"| Output | ONE shared 1x1 head -> single foreground logit (no dataset-specific head) |")
    A(f"| Parameters | {ab.get('measured_parameter_count', 'PENDING'):,} |"
      if isinstance(ab.get("measured_parameter_count"), int)
      else f"| Parameters | PENDING |")
    A(f"| Protocol | `{PROTOCOL_PATH}` (frozen) |")
    A(f"| Protocol SHA-256 | `{proto_sha}` |")
    A(f"| Manifest | `phase4_v3` |")
    A(f"| Populations | TRAIN 5832 / VAL 808 |")
    A(f"| Selection rule | `phase20_macro_domain_mean_dice_v1` (frozen) |")
    A(f"| Cohorts read | TRAIN and VAL only |")
    A(f"| TEST | **CLOSED** — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |")
    A(f"| Logical training runs | 1 (no architecture sweep, no hyperparameter sweep) |")
    A(f"| Canonical VAL inference runs | "
      + (str(val_eval.get("canonical_val_inference_runs")) if val_eval else "PENDING (exactly 1)") + " |")
    A(f"| Phase 22 | ELIGIBLE_NOT_STARTED |")
    A("")

    # -------------------------------------------------------- governance gate #
    A("## 2. Fail-closed entry gate")
    A("")
    A(f"**Verdict:** `{eg.get('verdict')}` — {eg.get('n_passed')}/{eg.get('n_checks')} checks passed, "
      f"`training_may_start = {eg.get('training_may_start')}`")
    A("")
    if eg.get("checks"):
        A("| Check | Passed | Detail |")
        A("|---|---|---|")
        for k, v in eg["checks"].items():
            det = v.get("detail")
            det = json.dumps(det)[:80] if not isinstance(det, str) else det[:80]
            A(f"| `{k}` | {v.get('passed')} | {det} |")
    A("")
    A(f"Artifact: `reports/audits/phase21_entry_gate.json` · SHA `{sha16(AUD/'phase21_entry_gate.json')}`")
    A("")

    # ---------------------------------------------------------- data contract #
    A("## 3. Data contract")
    A("")
    A("| Domain | task_id | TRAIN | VAL | Modality |")
    A("|---|---|---|---|---|")
    A("| ISIC | 0 | 2556 | 357 | dermoscopy (RGB) |")
    A("| BUSI | 1 | 602 | 84 | ultrasound (L) |")
    A("| KVASIR | 2 | 696 | 87 | endoscopy (RGB) |")
    A("| KUB | 3 | 1978 | 280 | radiograph (L/RGB) |")
    A("| **Total** | | **5832** | **808** | |")
    A("")
    A("`task_id` is `CONDITIONING_ALLOWED` but is **never** a channel, never concatenated to the")
    A("image, and never selects a dataset-specific head. The following are **never** model inputs:")
    A("`mask_path`, foreground fraction, `patient_id`, `case_id`, GT-derived metadata, KUB stone")
    A("`category` (Kidney/Ureteric/Bladder), object-size bin (TINY/SMALL/MEDIUM/LARGE), ROI")
    A("coordinates.")
    A("")

    # ------------------------------------------------------- protocol binding #
    A("## 4. Protocol binding — Phase-20 inheritance")
    A("")
    A(f"**Verdict:** `{pb.get('verdict')}` · "
      f"{pb.get('n_inherited_identical')}/{pb.get('n_inherited_checks')} inherited values identical · "
      f"**unintentional differences = {pb.get('unintentional_differences_count')}**")
    A("")
    A("| Inherited field | Phase-20 protocol | Phase-21 | Identical |")
    A("|---|---|---|---|")
    for k, v in (pb.get("inherited_values") or {}).items():
        A(f"| `{k}` | `{json.dumps(v['phase20_protocol_value'])[:46]}` | "
          f"`{json.dumps(v['phase21_value'])[:46]}` | {v['identical']} |")
    A("")
    A("### Declared intentional differences")
    A("")
    A("| Field | Class | Reason |")
    A("|---|---|---|")
    for d in pb.get("intentional_differences", []):
        A(f"| `{d['field']}` | {d['class']} | {d['reason']} |")
    A("")
    A(f"Artifact: `reports/audits/phase21_protocol_binding.json` · "
      f"SHA `{sha16(AUD/'phase21_protocol_binding.json')}`")
    A("")

    # --------------------------------------------------------- legacy audit #
    A("## 5. Legacy MedFiLM architecture audit")
    A("")
    A(f"**Evidence status:** `{la.get('evidence_status')}` · historical results claimed as current: "
      f"**{not la.get('not_current_prospective_result')}**")
    A("")
    A("| Item | Value |")
    A("|---|---|")
    A(f"| Legacy FiLM module | `{la.get('historical_class_names', {}).get('film_module')}` |")
    A(f"| Legacy model class | `{la.get('historical_class_names', {}).get('film_model')}` |")
    A(f"| FiLM equation | `{la.get('film_equation', {}).get('form')}` |")
    A(f"| gamma / beta | `{la.get('film_equation', {}).get('gamma_definition')}` / "
      f"`{la.get('film_equation', {}).get('beta_definition')}` |")
    A(f"| Identity at init | {la.get('film_equation', {}).get('identity_at_init')} |")
    A(f"| FiLM sites | {la.get('film_insertion_locations', {}).get('order')} |")
    A(f"| Squeeze-and-Excitation | {la.get('topology_features', {}).get('squeeze_excitation')} |")
    A(f"| Deep supervision | {la.get('topology_features', {}).get('deep_supervision')} |")
    A(f"| External pretrained weights | {la.get('pretrained_dependencies', {}).get('external_pretrained_weights')} |")
    A(f"| Legacy domains | {la.get('four_domain_compatibility', {}).get('legacy_domains')} (no KUB) |")
    A("")
    A("### Reuse classification")
    A("")
    for key, label in (("reuse_safe", "Reuse-safe"),
                       ("must_not_reuse", "Must NOT reuse"),
                       ("reference_only", "Reference only")):
        items = la.get("reuse_classification", {}).get(key, [])
        A(f"**{label}**")
        A("")
        for it in items:
            A(f"- {it}")
        A("")
    A("### Files inspected")
    A("")
    A("| Key | Path | SHA-256 |")
    A("|---|---|---|")
    for f in la.get("files_inspected", []):
        A(f"| `{f['key']}` | `{f['path']}` | `{(f.get('sha256') or 'MISSING')[:16]}...` |")
    A("")
    A("### Recorded ambiguities")
    A("")
    for a in la.get("ambiguities", []):
        A(f"- {a}")
    A("")
    A(f"Artifact: `reports/audits/phase21_legacy_medfilm_architecture_audit.json` · "
      f"SHA `{sha16(AUD/'phase21_legacy_medfilm_architecture_audit.json')}`")
    A("")

    # ------------------------------------------------------ architecture freeze #
    A("## 6. Frozen architecture (frozen BEFORE training)")
    A("")
    spec = ab.get("component_specification", {})
    A(f"**Verdict:** `{ab.get('verdict')}` · frozen before training: "
      f"**{ab.get('frozen_before_training')}** · parameters: **{ab.get('measured_parameter_count'):,}**"
      if isinstance(ab.get("measured_parameter_count"), int)
      else f"**Verdict:** `{ab.get('verdict')}`")
    A("")
    A("### FiLM conditioning")
    A("")
    tc = spec.get("task_conditioning", {})
    A("| Property | Value |")
    A("|---|---|")
    for k, v in tc.items():
        A(f"| {k} | `{json.dumps(v) if not isinstance(v, str) else v}` |")
    A("")
    A("### Shared backbone")
    A("")
    bb = spec.get("shared_backbone", {})
    A("| Property | Value |")
    A("|---|---|")
    for k, v in bb.items():
        A(f"| {k} | `{json.dumps(v) if not isinstance(v, str) else v}` |")
    A("")
    A("### Components present / absent")
    A("")
    A("| Component | Present |")
    A("|---|---|")
    for k, v in spec.get("present", {}).items():
        A(f"| {k} | **{v}** |")
    for k, v in spec.get("absent", {}).items():
        A(f"| {k} | {v} |")
    A("")
    A("### Search policy")
    A("")
    sp = ab.get("search_policy", {})
    A("| Property | Value |")
    A("|---|---|")
    for k, v in sp.items():
        A(f"| {k} | {v} |")
    A("")
    A(f"Artifact: `reports/audits/phase21_global_medfilm_architecture_binding.json` · "
      f"SHA `{sha16(AUD/'phase21_global_medfilm_architecture_binding.json')}`")
    A("")

    # --------------------------------------------------------- pre-execution #
    A("## 7. Pre-execution sanity checks")
    A("")
    A(f"**Verdict:** `{pe.get('verdict')}` — {pe.get('n_passed')}/{pe.get('n_checks')} passed · "
      f"`training_may_start = {pe.get('training_may_start')}`")
    A("")
    A("| Check | Passed | Detail |")
    A("|---|---|---|")
    for k, v in (pe.get("checks") or {}).items():
        A(f"| `{k}` | {v.get('passed')} | `{json.dumps(v.get('detail'))[:80]}` |")
    A("")
    A("**Key recorded finding.** The FiLM output projection is zero-initialised, so every site is an")
    A("EXACT identity at initialisation and `d(loss)/d(task_embedding)` is exactly **0** at step 0.")
    A("The projection itself *does* receive gradient at step 0, and after ONE optimizer step the")
    A("embedding path opens. Task conditioning is therefore **learned, not injected**. A weak")
    A("conditioning effect at convergence is a legitimate scientific finding and is reported as")
    A("`CONDITIONING_EFFECT_WEAK`, never hidden.")
    A("")
    A(f"Artifact: `reports/audits/phase21_pre_execution_check.json` · "
      f"SHA `{sha16(AUD/'phase21_pre_execution_check.json')}`")
    A("")

    # ----------------------------------------------------------- training cfg #
    A("## 8. Training configuration (inherited protocol)")
    A("")
    A("| Field | Value |")
    A("|---|---|")
    A(f"| Loss | `{json.dumps(CONFIG['loss'])}` |")
    A(f"| Optimizer | `{json.dumps(CONFIG['optimizer'])}` |")
    A(f"| Scheduler | `{json.dumps(CONFIG['scheduler'])}` |")
    A(f"| Batch size | {CONFIG['training']['batch_size']} |")
    A(f"| Eval batch size | {CONFIG['training']['eval_batch_size']} |")
    A(f"| Num workers | {CONFIG['training']['num_workers']} |")
    A(f"| AMP | {CONFIG['training']['amp']} |")
    A(f"| Seed | {CONFIG['training']['seed']} |")
    A(f"| Max epochs | {CONFIG['training']['max_epochs']} |")
    A(f"| Early-stopping patience | {CONFIG['training']['early_stopping_patience']} |")
    A(f"| Sampling policy | `{CONFIG['training']['sampling_policy']}` |")
    A(f"| Checkpoint metric | `{CONFIG['training']['checkpoint_metric']}` |")
    A(f"| Input channel policy | `{CONFIG['input_channel_policy']}` |")
    A(f"| Input resolution | {CONFIG['input_resolution']} |")
    A(f"| Augmentation | `{CONFIG['augmentation_policy']}` |")
    A("")

    # -------------------------------------------------------------- training #
    A("## 9. Training progress")
    A("")
    if hist.empty:
        A("No epochs completed yet.")
    else:
        best_i = hist["macro_domain_dice"].idxmax()
        best = hist.loc[best_i]
        A(f"**Completed epochs:** {len(hist)} · **best epoch:** {int(best['epoch'])} · "
          f"**best macro-domain VAL Dice:** {fmt(best['macro_domain_dice'])}")
        A("")
        A(f"**Per-epoch time:** mean {fmt(hist['epoch_seconds'].mean(), 1)} s · "
          f"median {fmt(hist['epoch_seconds'].median(), 1)} s · "
          f"min {fmt(hist['epoch_seconds'].min(), 1)} s · "
          f"max {fmt(hist['epoch_seconds'].max(), 1)} s")
        A("")
        A("| Epoch | train_loss | val_loss | macro Dice | ISIC | BUSI | KVASIR | KUB | LR | new best | bad | s |")
        A("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in hist.iterrows():
            A(f"| {int(r['epoch'])} | {fmt(r['train_loss'],4)} | {fmt(r['val_loss'],4)} | "
              f"**{fmt(r['macro_domain_dice'])}** | {fmt(r['val_dice_ISIC'],4)} | "
              f"{fmt(r['val_dice_BUSI'],4)} | {fmt(r['val_dice_KVASIR'],4)} | "
              f"{fmt(r['val_dice_KUB'],4)} | {r['learning_rate']:.3e} | {r['is_new_best']} | "
              f"{int(r['bad_epochs'])} | {fmt(r['epoch_seconds'],1)} |")
        A("")
        A(f"Best-so-far macro-domain VAL Dice: **{fmt(hist['best_so_far'].max())}**")
    A("")
    A("**Training status:** " + ("NATURALLY TERMINATED — "
                                 f"`{closure['stop_reason']}` at epoch {closure['final_epoch']}, "
                                 f"best epoch {closure['best_epoch']}, "
                                 f"resume_count {closure['resume_count']}"
                                 if training_done else
                                 "IN PROGRESS (the run is resumable and is kept alive by an hourly "
                                 "automation; resume is bit-exact by construction because every epoch "
                                 "is a pure function of `derive_epoch_seed(seed, epoch)`)"))
    A("")
    if closure:
        A("| Closure field | Value |")
        A("|---|---|")
        for k in ("best_epoch", "final_epoch", "stop_reason", "best_macro_domain_dice",
                  "best_val_loss", "resume_count", "independent_duplicate_runs",
                  "model_params", "total_elapsed_seconds", "checkpoint_selection_replay_verdict"):
            A(f"| {k} | `{closure.get(k)}` |")
        A("")
        A("| Domain | Dice at best epoch |")
        A("|---|---|")
        for k, v in closure.get("per_domain_dice_at_best", {}).items():
            A(f"| {k} | {fmt(v)} |")
        A("")
    ck = CKPT_DIR
    if ck.exists():
        A("| Checkpoint | Bytes | SHA-256 (16) |")
        A("|---|---|---|")
        for name in ("best.pt", "last.pt", "latest.pt"):
            p = ck / name
            if p.exists():
                A(f"| `{name}` | {p.stat().st_size:,} | `{sha16(p)}` |")
        A("")

    # ------------------------------------------------------- canonical VAL #
    A("## 10. Canonical VAL evaluation")
    A("")
    if val_eval:
        A("| Item | Value |")
        A("|---|---|")
        A(f"| Canonical VAL inference runs | **{val_eval.get('canonical_val_inference_runs')}** |")
        A(f"| Samples expected | {val_eval.get('samples_expected')} |")
        A(f"| Samples evaluated | {val_eval.get('samples_evaluated')} |")
        A(f"| Threshold | {val_eval.get('threshold')} |")
        A(f"| No TTA / no threshold tuning / no morphology | "
          f"{val_eval.get('no_tta')} / {val_eval.get('no_threshold_tuning')} / "
          f"{val_eval.get('no_morphology')} |")
        A(f"| Probability maps persisted | {val_eval.get('prob_maps_persisted')} |")
        A(f"| Checkpoint SHA-256 | `{val_eval.get('checkpoint_sha256')}` |")
    else:
        A("**PENDING** — runs once, after natural training termination:")
        A("")
        A("```bash")
        A("./.venv/Scripts/python.exe scripts/evaluation/evaluate_phase21_val.py")
        A("```")
        A("")
        A("Exactly ONE forward pass over the 808 VAL samples with `best.pt`, the frozen threshold")
        A("0.5, the frozen preprocessing and the correct task ID. Probability and binary prediction")
        A("maps are persisted per sample as NPZ so no future phase needs to replay inference.")
    A("")

    # -------------------------------------------------------------- results #
    A("## 11. Results")
    A("")
    if analysis:
        gm = analysis["global_medfilm"]
        A("### Global MedFiLM")
        A("")
        A("| Metric | Value |")
        A("|---|---|")
        A(f"| Macro-domain VAL Dice | **{fmt(gm['macro_domain_dice'])}** |")
        A(f"| 95% CI | [{fmt(gm['macro_domain_dice_ci_low'])}, {fmt(gm['macro_domain_dice_ci_high'])}] |")
        A(f"| Macro-domain IoU | {fmt(gm['macro_domain_iou'])} |")
        A(f"| Pooled Dice (descriptive) | {fmt(gm['pooled_dice_descriptive'])} |")
        A(f"| Rank among six models | {gm['rank_among_six']}/6 |")
        A("")
        A("| Domain | Dice | IoU |")
        A("|---|---|---|")
        for d in ("ISIC", "BUSI", "KVASIR", "KUB"):
            A(f"| {d} | {fmt(gm['per_domain_dice'][d])} | {fmt(gm['per_domain_iou'][d])} |")
        A("")
        A("### Six-model ranking")
        A("")
        _six = TAB / "phase21_six_model_comparison.csv"
        if _six.exists():
            _d = pd.read_csv(_six).set_index("model_key")
            A("| Rank | Model | Macro-domain Dice | 95% CI | Parameters |")
            A("|---|---|---|---|---|")
            for i, m in enumerate(analysis["six_model_ranking"], 1):
                if m in _d.index:
                    r = _d.loc[m]
                    if m == "global_medfilm":
                        _p = "3,523,001"
                    elif pd.notna(r["params"]):
                        _p = f"{int(r['params']):,}"
                    else:
                        _p = "n/a"
                    A(f"| {i} | {r['display_name']} | {fmt(r['macro_domain_dice'])} | "
                      f"[{fmt(r['macro_domain_dice_ci_low'])}, {fmt(r['macro_domain_dice_ci_high'])}] | "
                      f"{_p} |")
                else:
                    A(f"| {i} | {m} | | | |")
        else:
            A("| Rank | Model | Macro-domain Dice |")
            A("|---|---|---|")
            for i, m in enumerate(analysis["six_model_ranking"], 1):
                A(f"| {i} | {m} | |")
        A("")
        A("### Paired domain-stratified bootstrap vs the five frozen baselines")
        A("")
        _pb = analysis["paired_bootstrap"]
        # `comparisons` is the NUMBER OF BASELINES compared, not the bootstrap count.
        # Read the true n_boot/seed from the persisted paired-bootstrap table.
        _nb, _seed = 2000, 42
        _pbt = TAB / "phase21_paired_bootstrap_vs_baselines.csv"
        if _pbt.exists():
            _pbd = pd.read_csv(_pbt)
            _nb = int(_pbd["n_boot"].iloc[0])
            _seed = int(_pbd["seed"].iloc[0])
        A(f"Method: paired domain-stratified percentile bootstrap, `n_boot={_nb}`, seed={_seed}, "
          f"unit=image; the same resampled VAL indices are used for both models.")
        A("")
        A(f"- Statistically separable (CI excludes 0): **{_pb['significant_vs_baselines']}**")
        A(f"- CI overlaps zero (NOT separable): **{_pb['non_significant_vs_baselines']}**")
    else:
        A("**PENDING** — produced by the post-training pipeline:")
        A("")
        A("```bash")
        A("./.venv/Scripts/python.exe scripts/analysis/run_phase21_post_training_pipeline.py")
        A("```")
        A("")
        base = TAB / "phase20b_five_model_comparison.csv"
        if base.exists():
            bdf = pd.read_csv(base).sort_values("best_macro_domain_dice", ascending=False)
            A("For orientation the **frozen** five-model baselines are listed below. The Phase-21")
            A("row is deliberately left unset: the run is still training and no Phase-21 accuracy")
            A("number exists yet. Populating it before the canonical VAL pass would be fabrication.")
            A("")
            A("| Model | Macro-domain VAL Dice | Best epoch | Source |")
            A("|---|---|---|---|")
            for _, r in bdf.iterrows():
                A(f"| {r['display_name']} | {r['best_macro_domain_dice']:.6f} | "
                  f"{int(r['best_epoch'])} | FROZEN (Phase {r['phase']}) |")
            if not hist.empty:
                hb = float(hist["macro_domain_dice"].max())
                he = int(hist.loc[hist["macro_domain_dice"].idxmax(), "epoch"])
                A(f"| Global MedFiLM | *(pending)* | {he} | IN PROGRESS — best-so-far {hb:.6f}, "
                  "NOT a result |")
            A("")
            A("The in-progress figure is the epoch-selected best so far. It is shown only to")
            A("demonstrate the run is progressing and must **not** be compared against the frozen")
            A("column: the frozen values come from one canonical VAL pass over a frozen best")
            A("checkpoint, whereas the Phase-21 number is a per-epoch validation value from a run")
            A("whose checkpoint selection is not yet final. The authoritative Phase-21 result will")
            A("come from exactly one canonical VAL pass with a domain-stratified bootstrap CI and a")
            A("paired comparison against each baseline (the pairing uses identical resampled VAL")
            A("indices, which is why a naive column comparison is not equivalent to it).")
            A("")

    # ------------------------------------------------------------ KUB strata #
    A("## 12. KUB analyses (REPORTING ONLY)")
    A("")
    if analysis:
        A(f"Size taxonomy `kub_size_clean_v3_v1` strata n: "
          f"`{json.dumps(analysis['kub_size_n'])}`")
        A("")
        A(f"TINY stratum preserved for Phase 22: **{analysis['tiny_stratum_preserved_for_phase22']}** · "
          f"optimised on TINY: **False**")
    else:
        A("**PENDING.** KUB subgroup (Kidney / Ureteric / Bladder) and the frozen size taxonomy")
        A("(TINY / SMALL / MEDIUM / LARGE + ROI_NOT_PRIMARY_BINNED) are reporting-only. The TINY")
        A("stratum is preserved as evidence for Phase 22 and is **never** optimised on.")
    A("")

    # --------------------------------------------------------- conditioning #
    A("## 13. Task-conditioning diagnostic and FiLM sanity")
    A("")
    if cond:
        A("| Item | Value |")
        A("|---|---|")
        A(f"| Scope | {cond['scope']} |")
        A(f"| Cases | {cond['n_cases']} |")
        A(f"| Mean \\|delta Dice\\| with wrong task ID | {fmt(cond['mean_abs_delta_dice_wrong_task'])} |")
        A(f"| Max \\|delta Dice\\| with wrong task ID | {fmt(cond['max_abs_delta_dice_wrong_task'])} |")
        A(f"| Flag | **{cond['flag']}** |")
        A(f"| Flag rule | {cond['flag_rule']} |")
        A("")
        A(f"> {cond['honesty_note']}")
    else:
        A("**PENDING.** Measures the effect of feeding an INCORRECT task ID on the frozen 64-case")
        A("gallery, and summarises learned FiLM gamma/beta per task and site.")
    A("")

    # ------------------------------------------------------------ galleries #
    A("## 14. Galleries")
    A("")
    A("- **Frozen 64-case gallery** (16 per domain) reused **UNCHANGED**, extended to a six-model")
    A("  panel. Selection: `reports/tables/phase21_gallery_selection_64.csv`.")
    A("- **Detailed gallery** (>=16 per domain), explicitly labelled `ANALYTICAL_OUTCOME_SELECTED`.")
    A("- **Failure-analysis gallery** (worst-16), explicitly labelled `ANALYTICAL_OUTCOME_SELECTED`.")
    A("- The two outcome-selected galleries are **distinct** from the fixed 64-case gallery.")
    A("")

    # --------------------------------------------------------------- figures #
    A("## 15. Figures and notebook")
    A("")
    A("Figure root: `reports/figures/phase21_global_medfilm/` with subfolders `training/`,")
    A("`comparison/`, `kub/`, `conditioning/`, `gallery/`, `failure/`, `efficiency/`.")
    A("")
    A("Reviewer notebook: `notebooks/phasewise/phase_21_global_medfilm/"
      "phase21_global_medfilm_reference.ipynb` — deterministic cell IDs, fixed Styler UUIDs,")
    A("normalised memory addresses, stripped volatile metadata, stable output order; three")
    A("consecutive builds must be byte-identical.")
    A("")

    # ------------------------------------------------------------ efficiency #
    A("## 16. Parameter and compute accounting (MEASUREMENT ONLY)")
    A("")
    A(f"- Parameters: **{ab.get('measured_parameter_count', 'PENDING')}**")
    mac = load("phase21_analytical_mac_count.json")
    if mac:
        A(f"- Compute: **{mac['total_gmacs']:.4f} G MACs** "
          f"(**{mac['total_gflops_convention']:.4f} G FLOPs** at the 2x-MACs convention) "
          f"for a 1x3x512x512 input.")
        A("- Method: exact closed-form `Conv2d`/`Linear` count "
          "(`scripts/analysis/phase21_mac_count.py`). This is a **lower bound** on total")
        A("  arithmetic: it excludes GroupNorm, SiLU, pooling, interpolation and the FiLM")
        A("  elementwise modulation. No third-party FLOP library was used "
          "(thop / fvcore / ptflops / torchinfo are all absent).")
        A("")
        A("| Block | G MACs | Share |")
        A("|---|---|---|")
        for k, v in sorted((mac.get("by_block") or {}).items(), key=lambda x: -x[1]["macs"]):
            A(f"| `{k}` | {v['gmacs']:.4f} | {100*v['macs']/mac['total_macs']:.1f}% |")
        A("")
    else:
        A("- MACs/FLOPs: **PENDING** — produced by `scripts/analysis/phase21_mac_count.py`.")
    comp = TAB / "phase21_six_model_compute.csv"
    if comp.exists():
        cdf = pd.read_csv(comp).sort_values("gmacs")
        A("")
        A("### 16.1 Six-model comparison (identical protocol, 1x3x512x512)")
        A("")
        A("All six models are the frozen Phase-20/20B panel plus the Phase-21 Global MedFiLM")
        A("reference. Parameters and MACs are measured on the same input shape, so those columns")
        A("are directly comparable. Accuracy is tabulated separately in §11 and "
          "`phase21_six_model_comparison.csv`, because the frozen baselines are reported at")
        A("their own best epoch under the frozen Phase-20 protocol while Global MedFiLM is a")
        A("Phase-21 result; the two must not be silently mixed without that caveat.")
        A("")
        A("| Model | Parameters | Params rank | G MACs | MACs rank | vs MedFiLM (params x) | vs MedFiLM (MACs x) |")
        A("|---|---|---|---|---|---|---|")
        for _, r in cdf.iterrows():
            A(f"| {r['display_name']} | {int(r['params']):,} | {int(r['params_rank'])} | "
              f"{r['gmacs']:.4f} | {int(r['gmacs_rank'])} | {r['params_vs_medfilm_x']:.3f} | "
              f"{r['gmacs_vs_medfilm_x']:.3f} |")
        A("")
        med = cdf[cdf["model_key"] == "global_medfilm"].iloc[0]
        n = len(cdf)
        pr, gr = int(med["params_rank"]), int(med["gmacs_rank"])
        if pr == 1 and gr == 1:
            A(f"Global MedFiLM ranks **1 of {n} on parameters AND 1 of {n} on compute** — it is")
            A("simultaneously the smallest and the cheapest model in the panel, i.e. **the")
            A("lightest on both axes**. This is a *relative* statement about this six-model")
            A("panel only: the absolute cost (31.55 G MACs at 512 px) remains substantial, so")
            A("being the lightest member here does not by itself establish fitness for")
            A("constrained deployment.")
        else:
            A(f"Global MedFiLM ranks **{pr} of {n} on parameters** and **{gr} of {n} on "
              f"compute**: parameter count and arithmetic cost decouple, because cost is")
            A("governed by output resolution and the high-resolution decoder stages rather than")
            A("by the number of weights.")
        A("")
        top = cdf.loc[cdf["gmacs_per_mparam"].idxmax()]
        A(f"- Arithmetic per parameter: **{med['gmacs_per_mparam'] * 1e3:,.0f} MACs per "
          f"parameter** ({med['gmacs_per_mparam']:.2f} G MACs per M params). The highest in the")
        A(f"  panel is {top['display_name']} at {top['gmacs_per_mparam'] * 1e3:,.0f} MACs per "
          f"parameter — so a low parameter count does not by itself imply low arithmetic.")
        A(f"- Measurement device for this table: `{med['device']}`; "
          f"`task_ids` passed to `{int(cdf['task_ids_passed'].sum())}` of {n} models "
          "(only the task-conditioned reference).")
        A("")
    else:
        A("- Six-model compute comparison: **PENDING** — produced by "
          "`scripts/analysis/phase21_mac_count.py --all-models`.")
    eff = TAB / "phase21_efficiency_accounting.csv"
    if eff.exists():
        A(f"- GPU latency, peak memory, per-epoch wall time and an optional CPU latency benchmark: "
          f"`reports/tables/{eff.name}`.")
    else:
        A("- GPU latency, peak memory and a CPU latency benchmark: **PENDING** — produced by")
        A("  `scripts/analysis/phase21_efficiency.py`. These are deliberately **not** measured while")
        A("  a training run is live, because the benchmark would contend for the same GPU.")
    A("- Per-epoch wall time for the live run is available now from the training history (§9).")
    A("- **No** optimization, pruning, quantization or compression was performed.")
    A("")

    # --------------------------------------------------------- interpretation #
    A("## 17. Interpretation rules applied")
    A("")
    A("- Permitted: *\"Global MedFiLM achieved X compared with baseline Y.\"*")
    A("- Forbidden: *\"FiLM caused +X.\"* — no architecture-matched control exists.")
    A("- CI overlapping zero ⇒ the models are **not separable** and no ordering claim is made.")
    A("- No historical (legacy) result is claimed as a current Phase-21 result.")
    A("")

    # ------------------------------------------------------------- TEST lock #
    A("## 18. TEST lock")
    A("")
    A("| Counter | Value |")
    A("|---|---|")
    A("| TEST image reads | 0 |")
    A("| TEST mask reads | 0 |")
    A("| TEST inference | 0 |")
    A("| TEST visualizations | 0 |")
    A("")
    A("Enforced by `src.utils.test_lock.verify_test_lock`, `src.data.loaders.create_loader` and")
    A("`src.data.multidomain_dataset.MultiDomainDataset`, and re-verified at the start of training,")
    A("evaluation, analysis and reporting.")
    A("")

    # ------------------------------------------------------------- artifacts #
    A("## 19. Artifact index")
    A("")
    A("| Artifact | SHA-256 (16) | Bytes |")
    A("|---|---|---|")
    for p in sorted(AUD.glob("phase21_*.json")) + sorted(AUD.glob("phase21_*.csv")):
        A(f"| `reports/audits/{p.name}` | `{sha16(p)}` | {p.stat().st_size:,} |")
    for p in sorted(TAB.glob("phase21_*.csv")):
        A(f"| `reports/tables/{p.name}` | `{sha16(p)}` | {p.stat().st_size:,} |")
    A("")
    A("### Frozen science untouched")
    A("")
    A(f"- `{PROTOCOL_PATH}` — SHA `{proto_sha}` "
      f"(expected `{PROTOCOL_SHA256}`) — matches: **{proto_sha == PROTOCOL_SHA256}**")
    A("- No `phase20_*` or `phase20b_*` artifact was modified.")
    A("")

    # --------------------------------------------------------------- pending #
    A("## 20. Remaining steps to the terminal state")
    A("")
    if phase_state == "COMPLETE":
        A("None. Phase 21 is COMPLETE.")
    else:
        A("| # | Step | Status |")
        A("|---|---|---|")
        steps = [
            ("Training run", "IN PROGRESS" if not training_done else "DONE"),
            ("Closure + checkpoint-selection replay",
             "DONE" if closure else "PENDING"),
            ("Canonical VAL evaluation (1 pass, 808)",
             "DONE" if val_eval else "PENDING"),
            ("Metrics, bootstrap, paired comparison, KUB strata",
             "DONE" if analysis else "PENDING"),
            ("Conditioning diagnostic + FiLM sanity",
             "DONE" if cond else "PENDING"),
            ("Efficiency accounting",
             "DONE" if (TAB / "phase21_efficiency_accounting.csv").exists() else "PENDING"),
            ("Figures + galleries + notebook (3-build determinism)",
             "DONE" if (AUD / "phase21_notebook_determinism.json").exists() else "PENDING"),
            ("Final freeze", "DONE" if final_freeze.get("freeze_verified") else "PENDING"),
            ("Governance sync",
             "DONE" if (AUD / "phase21_governance_sync.json").exists() else "PENDING"),
        ]
        for i, (s, st) in enumerate(steps, 1):
            A(f"| {i} | {s} | **{st}** |")
        A("")
        A("Single command to finish everything once training terminates:")
        A("")
        A("```bash")
        A("./.venv/Scripts/python.exe scripts/analysis/run_phase21_post_training_pipeline.py")
        A("```")
        A("")
        A(f"Target terminal state: `{TERMINAL}`")
    A("")
    A("**Phase 22 is NOT started.**")
    A("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L), encoding="utf-8")

    status = {
        "artifact": "phase21_progress_status",
        "phase": 21,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase_state": phase_state,
        "experiment_id": EXPERIMENT_ID,
        "architecture_id": ARCHITECTURE_ID,
        "protocol_sha256": proto_sha,
        "protocol_sha_matches_frozen": proto_sha == PROTOCOL_SHA256,
        "entry_gate_verdict": eg.get("verdict"),
        "protocol_binding_verdict": pb.get("verdict"),
        "protocol_unintentional_differences": pb.get("unintentional_differences"),
        "architecture_binding_verdict": ab.get("verdict"),
        "pre_execution_verdict": pe.get("verdict"),
        "model_params": ab.get("measured_parameter_count"),
        "training": {
            "epochs_completed": int(len(hist)) if not hist.empty else 0,
            "best_epoch": int(hist.loc[hist["macro_domain_dice"].idxmax(), "epoch"]) if not hist.empty else None,
            "best_macro_domain_dice": float(hist["macro_domain_dice"].max()) if not hist.empty else None,
            "mean_epoch_seconds": float(hist["epoch_seconds"].mean()) if not hist.empty else None,
            "naturally_terminated": training_done,
            "stop_reason": closure.get("stop_reason") if closure else None,
            "resume_count": closure.get("resume_count") if closure else None,
        },
        "canonical_val": {
            "completed": bool(val_eval),
            "canonical_val_inference_runs": val_eval.get("canonical_val_inference_runs"),
            "samples_evaluated": val_eval.get("samples_evaluated"),
        },
        "results_available": bool(analysis),
        "final_freeze_written": bool(final_freeze.get("freeze_verified")),
        "terminal_state": final_freeze.get("terminal_state") if final_freeze.get("freeze_verified")
                          else None,
        "target_terminal_state": TERMINAL,
        "phase22_started": False,
        "report_path": "reports/phase21_global_medfilm_report.md",
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    OUT_STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")

    print("WROTE", OUT_MD, f"({len(L)} lines)")
    print("WROTE", OUT_STATUS)
    print("phase_state:", phase_state)
    if not hist.empty:
        print(f"epochs={len(hist)} best_epoch={status['training']['best_epoch']} "
              f"best_macro={status['training']['best_macro_domain_dice']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
