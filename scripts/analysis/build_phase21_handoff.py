"""Phase 21 — build a single self-contained handoff bundle for an external reviewer.

Purpose
-------
Produce ONE markdown file that contains everything an external model (e.g. ChatGPT)
needs in order to reason about Phase 21 and propose the next step, WITHOUT requiring
the repository or any file attachments.

Design rules
------------
* READ ONLY. This script never trains, never evaluates, never touches TEST, and never
  modifies any artifact. It only reads persisted files and concatenates them.
* Provenance is explicit: every embedded block is labelled with its source path and
  SHA-256, so the reviewer can tell what is verbatim vs summarised.
* The bundle is self-describing: it states the hard constraints, the frozen protocol,
  the exact numbers, the interpretation guard, and what is explicitly NOT done.
* If a source file is missing, it is reported as MISSING rather than silently skipped.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/build_phase21_handoff.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "reports" / "handoff" / "PHASE21_CHATGPT_HANDOFF.md"

EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
EXP_DIR = ROOT / "experiments" / EXP
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
NB = (ROOT / "notebooks" / "phasewise" / "phase_21_global_medfilm"
      / "phase21_global_medfilm_reference.ipynb")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def block(lines: list[str], title: str, path: Path, lang: str = "") -> None:
    """Embed a file verbatim with provenance, or record it as missing."""
    lines.append(f"### {title}")
    lines.append("")
    lines.append(f"`{path.relative_to(ROOT).as_posix()}`")
    lines.append("")
    if not path.exists():
        lines.append("> **MISSING** — expected but not found on disk.")
        lines.append("")
        return
    lines.append(f"- size: `{path.stat().st_size}` bytes")
    lines.append(f"- sha256: `{sha256(path)}`")
    lines.append("")
    lines.append(f"```{lang}")
    lines.append(path.read_text(encoding="utf-8").rstrip())
    lines.append("```")
    lines.append("")


def main() -> int:
    freeze = load(AUD / "phase21_final_freeze.json")
    prog = load(AUD / "phase21_progress_status.json")
    analysis = load(AUD / "phase21_analysis.json")
    val = load(AUD / "phase21_val_evaluation.json")
    cond = load(AUD / "phase21_task_conditioning_diagnostic.json")
    eff = load(AUD / "phase21_efficiency_accounting.json")
    det = load(AUD / "phase21_notebook_determinism.json")
    gov = load(AUD / "phase21_governance_sync.json")
    closure = load(EXP_DIR / "phase21_training_closure.json")
    proto = load(AUD / "phase20_shared_global_baseline_protocol.json")

    L: list[str] = []
    A = L.append

    A("# Phase 21 — Handoff Bundle for an External Reviewer (ChatGPT)")
    A("")
    A(f"Generated `{datetime.now(timezone.utc).isoformat()}` by "
      "`scripts/analysis/build_phase21_handoff.py`.")
    A("")
    A("**How to use this document.** It is a single self-contained snapshot of the "
      "Phase-21 experiment. Paste it whole into the external model and ask it for the "
      "next step. Everything below is read from persisted artifacts — nothing here is "
      "recomputed, and no file attachment is required.")
    A("")
    A("---")
    A("")

    # ------------------------------------------------------------------ 1. TL;DR
    A("## 1. TL;DR — status in one paragraph")
    A("")
    A(f"Phase 21 is **COMPLETE** and frozen. It trained exactly ONE shared four-domain "
      f"task-conditioned segmentation model (`Global MedFiLM`, architecture id "
      f"`{freeze.get('architecture_id', 'n/a')}`) on the frozen Phase-20 protocol. "
      f"Canonical VAL result: macro-domain Dice **{freeze.get('results', {}).get('macro_domain_dice', 'n/a')}** "
      f"on 808 VAL samples at a single threshold of 0.5. It ranks **1 of 6** on accuracy in "
      f"the panel and **1 of 6** on both parameters and compute, but a paired bootstrap says "
      f"it is **NOT separable from DeepLabV3+** (the runner-up) — the top two are tied. "
      f"Terminal state `{freeze.get('terminal_state', 'n/a')}`; Phase 22 is ELIGIBLE but "
      f"**NOT STARTED** by design.")
    A("")
    A("> **This is a GLOBAL reference model only.** It is NOT the final "
      "`RA-MedFiLM-Seg++`. No ROI proposal, no localizer, no regional refiner, no HR crop, "
      "no fusion, no benefit predictor, no router, no compression and no NAS were built or "
      "evaluated. TEST was never read.")
    A("")

    # ------------------------------------------------------------- 2. constraints
    A("## 2. Hard constraints that any proposed next step MUST respect")
    A("")
    A("These are standing rules for this repository. A next-step proposal that violates "
      "any of them is not admissible.")
    A("")
    A("| # | Constraint |")
    A("|---|---|")
    A("| 1 | **TEST is locked.** TEST image reads, mask reads, inference and visualization "
      "must all remain **0**. Never propose anything that reads TEST. |")
    A("| 2 | **One architecture frozen before training.** No hyperparameter sweep, no second "
      "seed, no architecture edits to the Phase-21 model. |")
    A("| 3 | **One canonical VAL pass.** It has already happened (808 samples, once). "
      "Never re-run it; any re-execution must use `--skip-eval`. |")
    A("| 4 | **Phase 22 must NOT be started** as a side effect. It is eligible, nothing more. |")
    A("| 5 | **No causal claim about FiLM.** There is no architecture-matched control (no "
      "identical plain model trained under this run), so only *\"Global MedFiLM achieved X "
      "compared with baseline Y\"* is permitted. *\"FiLM caused +X\"* is forbidden. |")
    A("| 6 | **CI overlap rule.** Where a paired confidence interval overlaps zero the models "
      "are NOT separable and no ordering claim may be made. |")
    A("| 7 | **The frozen Phase-20 protocol** (`phase20_shared_global_baseline_protocol.json`) "
      "and every `phase21_*_binding.json` / `*_pre_execution_check.json` are immutable. |")
    A("| 8 | **This is a GLOBAL reference only**, not the final RA-MedFiLM-Seg++. |")
    A("")

    # ------------------------------------------------------- 3. frozen protocol
    A("## 3. The frozen protocol (shared with Phase 20 — the comparison basis)")
    A("")
    A(f"Phase 21 inherited the frozen Phase-20 protocol **byte-for-byte**: protocol SHA "
      f"`{proto.get('protocol_sha256', proto.get('sha256', 'see file'))}`. "
      "The only intentional change is the architecture plus `task_id` conditioning. "
      "Full protocol below.")
    A("")
    block(L, "3.1 Frozen shared protocol", AUD / "phase20_shared_global_baseline_protocol.json",
          "json")
    if proto:
        A("**Protocol summary (key fields):**")
        A("")
        A("```json")
        keys = ["protocol_id", "protocol_sha256", "input_channel_policy", "input_resolution",
                "sampler", "loss", "optimizer", "scheduler", "batch_size", "eval_batch_size",
                "num_workers", "amp", "seed", "max_epochs", "early_stopping_patience",
                "selection_rule", "threshold"]
        sub = {k: proto[k] for k in keys if k in proto}
        A(json.dumps(sub, indent=2))
        A("```")
        A("")

    # -------------------------------------------------------- 4. what was trained
    A("## 4. What was trained")
    A("")
    arch = load(AUD / "phase21_global_medfilm_architecture_binding.json")
    A("| Field | Value |")
    A("|---|---|")
    A(f"| experiment id | `{EXP}` |")
    A(f"| architecture id | `{freeze.get('architecture_id', 'n/a')}` |")
    A(f"| parameters | `{freeze.get('results', {}).get('params', arch.get('params', 'n/a'))}` |")
    A(f"| is_global_reference_only | `{freeze.get('is_global_reference_only')}` |")
    A(f"| is_final_ra_medfilm_seg_plus_plus | `{freeze.get('is_final_ra_medfilm_seg_plus_plus')}` |")
    A("")
    A("Architecture in words: ONE shared residual encoder–decoder (channels 24/48/96/192/256, "
      "no squeeze-excite, no deep supervision) + a task embedding `nn.Embedding(4, 32)` + "
      "FiLM `F_hat = (1 + gamma(t)) * F + beta(t)` applied at **5 sites** (bridge, and "
      "decoder4..decoder1). `gamma`/`beta` are `tanh`-bounded and the FiLM output projection "
      "is **zero-initialised**, so the model is an **exact identity at initialisation** — "
      "conditioning is genuinely learned, not injected. ONE shared 1x1 foreground head.")
    A("")
    block(L, "4.1 Architecture binding (frozen)", AUD / "phase21_global_medfilm_architecture_binding.json",
          "json")

    # -------------------------------------------------------- 5. training outcome
    A("## 5. Training outcome")
    A("")
    tr = freeze.get("training", {})
    A("| Field | Value |")
    A("|---|---|")
    for k in ("epochs_completed", "best_epoch", "stop_reason", "resume_count",
              "mean_epoch_seconds", "total_training_seconds"):
        if k in tr:
            A(f"| {k} | `{tr[k]}` |")
    A(f"| naturally_terminated | see closure below |")
    A("")
    if closure:
        A("Note on `resume_count`: the host **tears down the launching process tree** every "
          "roughly 2–3.5 hours. The Phase-21 run was killed once this way (from epoch 29) and "
          "resumed; the trajectory is continuous. Resume is bit-exact **by construction** "
          "(per-epoch `derive_epoch_seed`, explicit generator + `seed_worker`, and a dataset "
          "with no internal RNG), which is why the checkpoints legitimately store no RNG state.")
        A("")
    block(L, "5.1 Training closure", EXP_DIR / "phase21_training_closure.json", "json")

    # ------------------------------------------------------------- 6. the result
    A("## 6. The result (canonical VAL, 808 samples, threshold 0.5)")
    A("")
    gm = analysis.get("global_medfilm", {})
    A("| Metric | Value |")
    A("|---|---|")
    A(f"| **macro-domain VAL Dice** | **{gm.get('macro_domain_dice')}** |")
    A(f"| 95% CI | [{gm.get('macro_domain_dice_ci_low')}, {gm.get('macro_domain_dice_ci_high')}] |")
    A(f"| macro-domain IoU | {gm.get('macro_domain_iou')} |")
    A(f"| pooled Dice (descriptive only) | {gm.get('pooled_dice_descriptive')} |")
    A(f"| rank among six models | {gm.get('rank_among_six')}/6 |")
    A("")
    pd_ = gm.get("per_domain_dice", {})
    A("| Domain | Dice | IoU |")
    A("|---|---|---|")
    for d in ("ISIC", "BUSI", "KVASIR", "KUB"):
        if d in pd_:
            A(f"| {d} | {pd_[d]} | {gm.get('per_domain_iou', {}).get(d)} |")
    A("")
    A("Bootstrap protocol: paired, domain-stratified, percentile; `n_boot=2000`, `seed=42`, "
      "resampling unit = image; **identical resampled VAL indices for both models** in every "
      "replicate. Paired comparison table below.")
    A("")
    block(L, "6.1 Paired bootstrap vs the five frozen baselines",
          TAB / "phase21_paired_bootstrap_vs_baselines.csv", "csv")
    A("**How to read that table.** A row is *separable* only when the CI excludes 0. "
      "Against `deeplabv3plus` the CI **includes 0** (p = 0.124), so Global MedFiLM and "
      "DeepLabV3+ are **tied** — do not claim a single winner. The other four baselines are "
      "separated.")
    A("")
    block(L, "6.2 Six-model accuracy comparison", TAB / "phase21_six_model_comparison.csv", "csv")
    block(L, "6.3 Frozen five-model panel (the citable baseline ranking)",
          TAB / "phase20b_five_model_comparison.csv", "csv")

    # ------------------------------------------------------------ 7. calibration etc
    A("## 7. Secondary analyses")
    A("")
    A("### 7.1 Task-conditioning diagnostic")
    A("")
    if cond:
        A(f"Verdict: **`{cond.get('verdict', cond.get('status', 'see file'))}`** — measured by "
          "re-scoring the frozen 64-case gallery with the WRONG task id. A large mean absolute "
          "Dice change means the conditioning is genuinely used.")
        A("")
    block(L, "Conditioning diagnostic artifact", AUD / "phase21_task_conditioning_diagnostic.json",
          "json")

    A("### 7.2 KUB size strata (REPORTING ONLY)")
    A("")
    A("KUB is stratified by a frozen taxonomy (`kub_size_clean_v3_v1`) using connected-8 "
      "components on the foreground (`mask > 0`), FULL_FIELD only. **These strata are a "
      "reporting device, never a selection or promotion criterion.**")
    A("")
    kub = analysis.get("kub_size_n", {})
    if kub:
        A(f"Gallery stratum counts: `{json.dumps(kub)}`")
        A("")

    A("### 7.3 Cost / efficiency")
    A("")
    if eff:
        A("| Metric | Value | Unit |")
        A("|---|---|---|")
        for k in ("measured_parameter_count", "macs", "gmacs", "gflops_2x",
                  "gpu_latency_median_batch1", "gpu_peak_memory_batch1",
                  "gpu_latency_median_batch8", "gpu_peak_memory_batch8",
                  "cpu_latency_median_batch1", "cpu_latency_median_batch4",
                  "mean_epoch_seconds", "total_training_seconds"):
            if k in eff:
                v = eff[k]
                A(f"| {k} | {v.get('value') if isinstance(v, dict) else v} | "
                  f"{v.get('unit', '') if isinstance(v, dict) else ''} |")
        A("")
        A("The MAC count is an **exact closed-form Conv2d/Linear count** and therefore a "
          "**LOWER BOUND** — it excludes norm, activation, pooling, interpolation and the "
          "element-wise FiLM ops. Cost is resolution-driven: the three stride-1 decoder stages "
          "each account for ~18.7% of total arithmetic.")
        A("")
    block(L, "Six-model compute table", TAB / "phase21_six_model_compute.csv", "csv")

    A("### 7.4 Figure + notebook inventory")
    A("")
    if det:
        A(f"- notebook builds: `{det.get('builds')}` "
          f"(three byte-identical: `{det.get('three_builds_byte_identical')}`)")
        A(f"- notebook path: `{det.get('notebook_path')}`")
        A("")
    fig_inv = load(ROOT / "reports" / "figures" / "phase21_global_medfilm"
                   / "phase21_figure_inventory.json")
    if fig_inv:
        A(f"- figures produced: **{fig_inv.get('n_figures')}** "
          f"(embedded in notebook: {fig_inv.get('n_embedded_in_notebook', fig_inv.get('n_embedded'))})")
        A("")

    # ----------------------------------------------------------- 8. full report
    A("## 8. Full Phase-21 report (verbatim)")
    A("")
    A("The complete reviewer-facing report follows. This is the authoritative narrative "
      "and it supersedes anything summarised above.")
    A("")
    block(L, "Phase-21 report", ROOT / "reports" / "phase21_global_medfilm_report.md", "markdown")

    # --------------------------------------------------------- 9. consolidated table
    A("## 9. Consolidated all-trained-models comparison")
    A("")
    A("Every previously trained model in the project, on one page, with explicit "
      "**FROZEN vs LIVE** provenance.")
    A("")
    block(L, "All trained models", TAB / "phase21_all_trained_models_comparison.md", "markdown")

    # ----------------------------------------------------------- 10. governance
    A("## 10. Governance and freeze evidence")
    A("")
    A("| Check | Result |")
    A("|---|---|")
    A(f"| freeze_verified | `{freeze.get('freeze_verified')}` |")
    A(f"| validation_problems | `{freeze.get('validation_problems')}` |")
    A(f"| terminal_state | `{freeze.get('terminal_state')}` |")
    A(f"| phase22_eligible | `{freeze.get('phase22_eligible')}` |")
    A(f"| phase22_started | `{freeze.get('phase22_started')}` |")
    g = freeze.get("governance", {})
    for k in ("test_reads_total_observed", "test_lock_clean", "manifest_version",
              "val_population", "train_population"):
        if k in g:
            A(f"| {k} | `{g[k]}` |")
    A("")
    A("### 10.1 Interpretation guard (binding on any write-up)")
    A("")
    interp = freeze.get("interpretation", {})
    A(f"- **PERMITTED:** {interp.get('permitted', 'n/a')}")
    A(f"- **FORBIDDEN:** {interp.get('forbidden', 'n/a')}")
    A(f"- **Reason:** {interp.get('reason', 'n/a')}")
    A(f"- **CI-overlap rule:** {interp.get('ci_overlap_rule', 'n/a')}")
    A("")
    block(L, "10.2 Final freeze artifact (authoritative)", AUD / "phase21_final_freeze.json", "json")
    block(L, "10.3 Progress status", AUD / "phase21_progress_status.json", "json")
    block(L, "10.4 Governance sync (additive only)", AUD / "phase21_governance_sync.json", "json")

    # ------------------------------------------------------- 11. repo conventions
    A("## 11. Repository conventions the reviewer should assume")
    A("")
    A("| Item | Convention |")
    A("|---|---|")
    A("| Manifest | `manifests/phase4_v3/` — TRAIN 5832 / VAL 808 / TEST 1683 / QUARANTINED 118. "
      "Root `manifests/*.csv` are the OLD frozen phase4_v2 set: never load. |")
    A("| Foreground mask | `mask > 0` (connectivity 8) — never `mask == 1` |")
    A("| Preprocessing | aspect-preserving resize + centre pad, `scale = min(s/w, s/h)`, "
      "sizes {256, 512, 768, 1024}; Phase-21 model uses RGB 3ch at 512 px |")
    A("| Metrics | Dice/IoU at threshold 0.5, eps 1e-7 |")
    A("| Determinism | TRAIN is stochastic (augmentation); VAL is deterministic. Bitwise GPU "
      "determinism is NOT claimed. |")
    A("| Run artifacts | `experiments/<id>/` holds history/state/config/closure; "
      "`checkpoints/<id>/` holds ONLY best/last/latest `.pt` |")
    A("| Result presentation | Stock convention: **increase = red, decrease = green**, "
      "currency ¥ (for any charts) |")
    A("")
    A("### 11.1 Task / domain ids")
    A("")
    A("| task_id | Domain | Notes |")
    A("|---|---|---|")
    A("| 0 | ISIC 2018 | RGB, dermoscopy |")
    A("| 1 | BUSI | grayscale, ultrasound |")
    A("| 2 | Kvasir-SEG | RGB, endoscopy |")
    A("| 3 | KUB | grayscale/RGB, radiography |")
    A("")

    # --------------------------------------------------------- 12. open questions
    A("## 12. Open questions / what legitimately comes next")
    A("")
    A("Phase 21 answered a narrow question: *does a single shared, task-conditioned "
      "network hold up against five per-domain baselines under one frozen protocol?* It does, "
      "as a **GLOBAL reference**. What is deliberately NOT established:")
    A("")
    A("1. **No causal attribution to FiLM** — there is no architecture-matched plain control "
      "trained under this run. A control run would be needed to isolate the conditioning effect.")
    A("2. **Global MedFiLM vs DeepLabV3+ is a tie**, not a win (CI spans zero, p = 0.124).")
    A("3. **No deployment claim.** 31.55 G MACs at 512 px is the lightest in the panel, but "
      "that is a *relative* statement; nothing here shows fitness for constrained hardware.")
    A("4. **No compression / distillation / NAS / pruning work** has been done.")
    A("5. **No ROI, localizer, regional refiner, fusion, benefit predictor or router** — the "
      "full `RA-MedFiLM-Seg++` is untouched.")
    A("6. **KUB is the bottleneck** for every model in the panel (best KUB Dice ≈ 0.764 here).")
    A("")

    # ------------------------------------------------------------ 13. hashes
    A("## 13. Artifact hash index")
    A("")
    A("Use these to confirm the reviewer is reasoning about exactly this revision.")
    A("")
    A("| Artifact | sha256 |")
    A("|---|---|")
    srcs = [
        AUD / "phase21_final_freeze.json",
        AUD / "phase21_analysis.json",
        AUD / "phase21_val_evaluation.json",
        TAB / "phase21_paired_bootstrap_vs_baselines.csv",
        TAB / "phase21_six_model_comparison.csv",
        TAB / "phase21_six_model_compute.csv",
        TAB / "phase21_all_trained_models_comparison.md",
        ROOT / "reports" / "phase21_global_medfilm_report.md",
        EXP_DIR / "phase21_training_closure.json",
        NB,
    ]
    for p in srcs:
        A(f"| `{p.relative_to(ROOT).as_posix()}` | `{sha256(p)}` |")
    A("")

    A("---")
    A("")
    A("## 14. Suggested prompt to hand to the external reviewer")
    A("")
    A("> You are reviewing a completed machine-learning experiment, Phase 21 of a "
      "phase-wise medical image segmentation project. The attached document is a complete, "
      "self-contained snapshot: status, frozen protocol, architecture, results, statistical "
      "comparisons, cost, governance evidence, and the explicit constraints. "
      "Read section 2 (hard constraints) and section 10.1 (interpretation guard) first — "
      "they are binding. Section 12 lists what is deliberately NOT established. "
      "Then propose the single best next step for this project, and justify it against the "
      "constraints. If your proposal requires reading the TEST split, re-running the canonical "
      "VAL pass, changing the frozen protocol, or starting Phase 22, it is not admissible. "
      "State explicitly which open question in section 12 your proposal addresses.")
    A("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"WROTE {OUT}")
    print(f"lines: {len(L)} | bytes: {OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
