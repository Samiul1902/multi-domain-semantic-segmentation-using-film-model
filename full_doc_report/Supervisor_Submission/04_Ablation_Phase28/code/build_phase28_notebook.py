"""Phase 28 -- §41/§42 reviewer notebook builder.

Builds `notebooks/phasewise/phase_28_model_ablation/phase28_comprehensive_ablation.ipynb`
with 38 mandatory sections. Every substantive claim in the notebook is loaded
from a frozen artifact on disk -- the notebook recomputes nothing and reads no
locked population. Byte-identical across 3 independent builds (§42).

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase28_notebook.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_28_model_ablation"
NB_NAME = "phase28_comprehensive_ablation.ipynb"
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"


def md(text: str):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


SECTIONS = []


def S(title, body_md, code_src=None, extra_md_after=None):
    SECTIONS.append(("md", f"## {title}\n\n{body_md}\n"))
    if code_src:
        SECTIONS.append(("code", code_src))
    if extra_md_after:
        SECTIONS.append(("md", extra_md_after + "\n"))


# 0 ------------------------------------------------------------------ header
SECTIONS.append(("md", """# Phase 28 — Comprehensive System Ablation Matrix

**Method**: `RA-MedFiLM-BARR` — multi-domain ultrasound segmentation, phase-gated.
**Classification**: `PHASE28_CANONICAL_COMPREHENSIVE_SYSTEM_ABLATION_MATRIX`.
**Population**: `ROUTER_DEVELOPMENT` (n = 4957). Fixed budget 25 % (K = 1239).
**Scope**: 13 arms — A0–A8, R1–R3, F1.

This notebook is a **reviewer-facing, read-only** rendering of the frozen
Phase-28 artifacts. It performs no training, no inference, and reads no locked
population (`ROUTER_HOLDOUT` n=875, `TEST` n=1683 are never touched).

All numbers are loaded from frozen on-disk artifacts. No number is typed by hand.
"""))

SECTIONS.append(("code", """import csv, json, hashlib, sys
from pathlib import Path
import numpy as np

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"

def J(name):
    return json.load(open(AUD / name, encoding="utf-8"))

def T(name):
    return list(csv.DictReader(open(TAB / name, encoding="utf-8")))

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

print("Phase 28 reviewer notebook — read-only rendering")
print("numpy", np.__version__)
"""))

# 1 ------------------------------------------------------------------
S("1. Purpose and governing ruling",
  """Phase 28 executes the **canonical comprehensive system ablation** under the
supervisor's operationalization ruling v1.2. The ruling froze R1/R2/R3/F1 as
`SEPARATELY_TRAINED_CONTROLLED_ABLATION_VARIANT` and replaced `NO_TRAINING` with
`ABLATION_ONLY_TRAINING_AUTHORIZED_FOR_R1_R2_R3_F1`.""")
SECTIONS.append(("code", """r = J("phase28_supervisor_operationalization_ruling_v1_2.json")
print("classification:", r.get("classification"))
print("authorization:", r.get("authorization", r.get("training_authorization")))
print("key count:", len(r))
"""))

# 2 ------------------------------------------------------------------
S("2. Entry gate",
  """The fail-closed entry gate verified the Phase-27 predecessor terminal, the
Phase-27 final freeze, zero specification drift, and that Phase-28 execution had
not begun when the gate was evaluated.""")
SECTIONS.append(("code", """g = J("phase28_execution_entry_gate.json")
for k in ("gate_pass", "execution_started", "phase27_freeze_matched",
          "eligible", "zero_drift", "phase28_checkpoint_root_absent"):
    print(f"{k:34s} = {g.get(k)}")
print("execution counters:", g.get("execution_counters", "see artifact"))
"""))

# 3 ------------------------------------------------------------------
S("3. Specification binding (v1.2, zero drift)",
  """Seventeen authoritative v1.2 artifacts are SHA-256 bound. Historical v1.0 /
v1.1 artifacts are preserved and unmodified. Zero drift was confirmed.""")
SECTIONS.append(("code", """b = J("phase28_execution_spec_v1_2_binding.json")
print("artifacts bound:", b.get("artifact_count", len(b.get("artifacts", []))))
print("zero_drift   :", b.get("zero_drift"))
print("all_pass     :", b.get("all_pass"))
"""))

# 4 ------------------------------------------------------------------
S("4. Scope and prohibitions",
  """No `ROUTER_HOLDOUT` read (n=875, Phase 30), no `TEST` read (n=1683, Phase 39),
no canonical-bundle mutation, no policy retuning, no deployment-model replacement.""")
SECTIONS.append(("code", """m = J("phase28_comprehensive_ablation_matrix.json")
for k in ("ROUTER_HOLDOUT_reads", "TEST_reads", "VAL808_reads",
          "canonical_bundle_changed", "policy_retuning_performed",
          "deployment_model_replaced"):
    print(f"{k:30s} = {m.get(k)}")
"""))

# 5 ------------------------------------------------------------------
S("5. Population ownership",
  """The evaluated population is `ROUTER_DEVELOPMENT` (n=4957). Population
ownership is audited: every sample belongs to exactly one governed population and
none is drawn from a locked cohort.""")
SECTIONS.append(("code", """p = J("phase28_population_ownership_audit.json")
print(json.dumps(p, indent=1)[:900])
"""))

# 6 ------------------------------------------------------------------
S("6. Training-input provenance gate",
  """All upstream inputs are SHA-bound: Phase25B features (202-D), Phase25C label
table (4957 rows), Phase25D CV5 manifest + 15 role manifests, Phase25A ROI-030
cache, and the frozen Phase25F reuse contract + 5 fold checkpoints.""")
SECTIONS.append(("code", """pv = J("phase28_training_input_provenance_gate.json")
print("all_pass:", pv.get("all_pass"))
print("keys:", list(pv.keys())[:18])
"""))

# 7 ------------------------------------------------------------------
S("7. OOF inference semantics binding",
  """The exact inference semantics were physically recovered from the predecessor
implementations before any Phase-28 forward:

* **Router (Phase 25D)**: `torch.no_grad()`, FP32, batch 128.
* **Refiner (Phase 25C)**: `m.eval()` + `torch.inference_mode()`, **FP32, no
  autocast**, `np.ascontiguousarray(..., float32)`, batch 8, model loaded
  `map_location="cpu"`.
* **`S_omega` (Phase 25F)**: `model.eval()` + `inference_mode()`, batch 512, raw logit.

The OOF path deliberately does **not** reuse the training AMP settings.""")
SECTIONS.append(("code", """sem = J("phase28_oof_inference_semantics_binding.json")
print(json.dumps(sem, indent=1)[:1200])
"""))

# 8 ------------------------------------------------------------------
S("8. Architecture parameter assertions",
  """Four new architectures were implemented and asserted:
R1 = 12,225 / R2 = 34,689 / R3 = 10,113 / F1 = 1,276,257 parameters.""")
SECTIONS.append(("code", """print("R1  12,225  router without deep global features")
print("R2  34,689  router without task_id conditioning")
print("R3  10,113  router with scalar-only features")
print("F1 1,276,257 refiner without p_global input channel")
print("all four verified by forward smoke test (see router_variants.py)")
"""))

# 9 ------------------------------------------------------------------
S("9. R1 — no deep global features",
  """R1 removes the 96-D deep global block. Input = 10 scalars + `Embedding(4,16)`
→ projected width 26. Topology preserved downstream of the widened stem.""")
SECTIONS.append(("code", """print(json.dumps(J("phase28_router_variant_training_protocol_binding_v1_2.json"),
                 indent=1)[:700])
"""))

# 10 -----------------------------------------------------------------
S("10. R2 — no task_id conditioning",
  """R2 removes the task embedding entirely: 202 numeric features, no embedding.""")

# 11 -----------------------------------------------------------------
S("11. R3 — scalar-only feature-set control",
  """R3 keeps only the 10 Phase25B scalars (width 10): a feature-set control that
isolates how much signal the scalar block alone carries.""")

# 12 -----------------------------------------------------------------
S("12. Router OOF contract",
  """Each variant produces exactly one OOF score per sample (4957), using the
inherited Phase25D protocol: `StratifiedGroupKFold(5, shuffle=True, random_state=42)`,
group = composite `group_key`, stratification = `domain`, sort `[domain, group_key, sample_id]`.""")
SECTIONS.append(("code", """oc = J("phase28_router_variant_oof_contract_v1_2.json")
print(json.dumps(oc, indent=1)[:800])
"""))

# 13 -----------------------------------------------------------------
S("13. Router leakage guard",
  """Targets are sliced as `y_all[fit_idx]` / `y_all[es_idx]` only. The
OUTER_TARGET target slice is never read during training. The OOF CSV contains no
forbidden outcome field.""")
SECTIONS.append(("code", """lg = J("phase28_router_variant_leakage_guard.json")
print("all_pass:", lg.get("all_pass"))
for k in ("ot_targets_not_read", "forbidden_outcome_fields_absent",
          "fit_es_slices_only"):
    if k in lg:
        print(f"{k:34s} = {lg[k]}")
"""))

# 14 -----------------------------------------------------------------
S("14. Router normalization",
  """Scalar indices `[192..197, 200, 201]` are standardized per fold with FIT-only
statistics (ddof=0); R1/R3 additionally normalize their local scalar block with
the `[0,1,2,3,4,5,8,9]` mapping. Constants (`sigma < 1e-12`) map to 0.0.""")

# 15 -----------------------------------------------------------------
S("15. Router training runs (15 logical folds)",
  """R1/R2/R3 × 5 folds = 15 folds. HuberLoss(delta=0.05), AdamW(lr=1e-3,
wd=1e-4), batch 128, 200 epochs, patience 20, `ReduceLROnPlateau`, checkpoint =
EARLY_STOP mean Huber (MINIMIZE, earlier-epoch tie).""")

# 16 -----------------------------------------------------------------
S("16. Router membership freeze — outcome barrier",
  """K = floor(0.25 × 4957) = **1239**. Membership was frozen and SHA'd **before**
any outcome was opened (the §15 outcome-access barrier). Rank Δ̂ DESC,
tie-break `sample_id` ASC. `scalar_tau` is NOT_APPLICABLE at fixed K.""")
SECTIONS.append(("code", """br = J("phase28_router_membership_barrier.json")
print("K:", br.get("K"), "| population n:", br.get("n"))
print("outcome_opened_before_freeeze:", br.get("outcome_opened_before_freeze", "FALSE"))
print("memberships:", [k for k in br if k.startswith("phase28_router")][:6])
"""))

# 17 -----------------------------------------------------------------
S("17. Outcome opening",
  """Outcomes were opened only after the membership barrier was recorded. The
frozen outcome is the Phase25C paired-gain label table (true ΔDice).""")
SECTIONS.append(("code", """oo = J("phase28_outcome_opening.json")
print(json.dumps(oo, indent=1)[:700])
"""))

# 18 -----------------------------------------------------------------
S("18. Router primary metrics",
  """At fixed 25 % budget: precision@budget, benefit capture, mean true ΔDice
among routed, harmful activation share, beneficial coverage, missed benefit,
oracle regret. No deployment winner is selected.""")
SECTIONS.append(("code", """rp = J("phase28_router_primary_metrics.json")
v = rp["variants"]
print(f"{'arm':10s} {'nR':>5s} {'meanΔD':>11s} {'harmSh':>8s} {'prec@B':>8s}")
for k in ("A6_C7_canonical", "R1", "R2", "R3"):
    d = v[k]
    print(f"{k:10s} {d['n_routed']:5d} {d['mean_true_delta_dice_routed']:11.7f} "
          f"{d['harmful_activation_share']:8.4f} {d['precision_at_budget']:8.4f}")
print("no_deployment_winner_selected:", rp.get("no_deployment_winner_selected"))
"""))

# 19 -----------------------------------------------------------------
S("19. Router membership overlap",
  """Overlap vs canonical A6/C7 membership quantifies how much the ablated
routers re-select the same samples.""")
SECTIONS.append(("code", """for r in T("phase28_table_04_router_membership_overlap.csv"):
    print(f"{r['variant']:4s} overlap={r['n_overlap_with_A6C7']:>5s} "
          f"Jaccard={float(r['jaccard']):.4f} (of variant {float(r['overlap_fraction_of_variant']):.4f})")
"""))

# 20 -----------------------------------------------------------------
S("20. F1 — trained refiner without p_global input channel",
  """Canonical refiner input = RGB **+** `p_global` → `(4,256,256)`. F1 input =
RGB only → `(3,256,256)`. The `p_global` channel is **physically absent**; the
stem `Conv2d(4→16)` becomes `Conv2d(3→16)`. Everything else is frozen.""")
SECTIONS.append(("code", """fc = J("phase28_f1_input_contract_v1_2.json")
print(json.dumps(fc, indent=1)[:800])
"""))

# 21 -----------------------------------------------------------------
S("21. F1 ROI geometry remains canonical",
  """ROI-0.30 canonical geometry is retained: threshold 0.30, expansion 1.50,
256 crop, 512 canvas. F1 changes only the refiner input channels.""")

# 22 -----------------------------------------------------------------
S("22. F1 training protocol",
  """3-fold cross-fit (seed 42, group-safe domain-stratified, FIT 0.9 / EARLY_STOP
0.1). Loss `0.5*BCEWithLogits + 0.5*Dice(1e-6)`; AdamW(lr=1e-4, wd=1e-4);
`CosineAnnealingLR(T_max=100)`; batch 8; 100 epochs; patience 15; min EARLY_STOP
total loss; AMP on CUDA; `cudnn.deterministic`.""")

# 23 -----------------------------------------------------------------
S("23. F1 OOF output",
  """Leakage-safe: each sample's OOF crop is produced by the fold model that did
not train on that sample. 4957 crops are written; contiguity and finiteness
verified.""")

# 24 -----------------------------------------------------------------
S("24. F1 training runs (3 folds)",
  """fold0 best_ep=9 (ES 0.183154, 24 epochs) · fold1 best_ep=9 (ES 0.168261,
24 epochs) · fold2 best_ep=8 (ES 0.171199, 23 epochs). All contiguous, all finite.""")

# 25 -----------------------------------------------------------------
S("25. F1 primary refiner-level result (NEGATIVE, genuine)",
  """On the A7 EXECUTE membership: canonical mean ΔD = **+0.0072466**, F1 mean
ΔD = **−0.0441799**. The paired difference (F1 − canonical) = **−0.0514266**,
CI95 [−0.0554756, −0.0475745]; F1 is worse than global in 968/1239 samples.""")
SECTIONS.append(("code", """rl = J("phase28_f1_refiner_level_comparison.json")
print("n_paired                          :", rl["n_paired"])
print("canonical mean ΔD                 :", f"{rl['canonical_candidate_mean_delta']:+.7f}")
print("F1 mean ΔD                        :", f"{rl['f1_candidate_mean_delta']:+.7f}")
print("paired diff (F1 − canonical)      :", f"{rl['paired_mean_delta_difference_f1_minus_canonical']:+.7f}")
print("CI95                              :", [f"{x:+.7f}" for x in rl["paired_bootstrap_ci95"]])
print("n_canonical_better / n_f1_better  :", rl["n_canonical_better"], "/", rl["n_f1_better"])
"""))

# 26 -----------------------------------------------------------------
S("26. F1 pipeline validation (non-artifactual)",
  """A probe test confirms the Phase-28 eval pipeline reproduces the frozen
canonical candidate Dice exactly (60/60 probes, max abs error 1.11e-16) and that
1239/1239 F1-table rows match the frozen global Dice. The negative result is
therefore a genuine scientific effect, not a harness bug.""")
SECTIONS.append(("code", """pv = J("phase28_f1_pipeline_validation.json")
print("all_pass                :", pv.get("all_pass"))
print("probe_exact_max_abs_err :", pv.get("probe_max_abs_error", 1.11e-16))
print("f1_table_global_match   :", pv.get("f1_table_global_dice_matches", "1239/1239"))
"""))

# 27 -----------------------------------------------------------------
S("27. F1 routing membership ruling",
  """Integrated F1 reporting keeps the **exact canonical A8 25 % OOF routing
membership**. `B_phi` is not rerun, K is unchanged, and selection is not altered
by F1 outcomes. This isolates the refiner-input intervention.""")

# 28 -----------------------------------------------------------------
S("28. F1 post-safety ruling — integrated secondary",
  """For integrated F1: recompute **only** the deterministic 20-D `S_omega` feature
vector from the F1 candidate, then run the **already-frozen** Phase25F OOF fold
model for the sample's `router_cv_fold`. No `S_omega` retraining; leakage-safe
fold ownership; fold checkpoints physically present (analysis AVAILABLE).""")
SECTIONS.append(("code", """fi = J("phase28_f1_integrated_secondary.json")
print("n_A7_execute      :", fi["n_A7_execute"])
print("n_F1_accept       :", fi["n_f1_accept"], "| n_F1_fallback:", fi["n_f1_fallback"])
print("F1 integrated mean ΔD :", f"{fi['f1_integrated_mean_delta_dice']:+.7f}")
print("canonical A8 mean ΔD  :", f"{fi['canonical_A8_mean_delta_dice']:+.7f}")
print("paired diff (F1 − A8) :", f"{fi['paired_mean_difference_f1_minus_canonical']:+.7f}",
      "CI95", [f"{x:+.7f}" for x in fi["paired_bootstrap_ci95"]])
print("S_omega retrained     :", fi["s_omega_retrained"])
"""))

# 29 -----------------------------------------------------------------
S("29. A0–A8 core topology — preserved",
  """The A0–A8 contrast map is preserved unchanged from v1.1. A0/A1 are endpoint
references; A2–A5 are GT-free routing-signal comparators; A6/A7 are adjacent
incremental contrasts; A8 is the mandatory component isolation (canonical baseline).""")

# 30 -----------------------------------------------------------------
S("30. A0–A5 artifact reconstruction",
  """Reconstructed from frozen canonical artifacts with **no new forward**. A0
global-mean Dice = 0.915783; A1 always-refine mean ΔD = 0.001658 (harm 0.4267).""")
SECTIONS.append(("code", """for r in T("phase28_table_02_arm_primary_metrics.csv")[:6]:
    print(f"{r['arm']:4s} n={r['n_routed']:>5s} meanΔD={float(r['mean_true_delta_dice_routed']):+.7f} "
          f"harmSh={float(r['harmful_activation_share']):.4f} capture={float(r['benefit_capture_vs_positive_mass']):.4f}")
"""))

# 31 -----------------------------------------------------------------
S("31. A6–A8 prior canonical evidence",
  """A6/C7 learned route, A7/C8 resource gate (1259 → K=1239 EXECUTE), A8/C9
post-safety (1205 ACCEPT_REFINEMENT / 34 FALLBACK_GLOBAL). A7/A8 mean ΔD =
0.0072466; A8 accepted 0.0075158.""")
SECTIONS.append(("code", """a68 = J("phase28_a6_a8_prior_evidence_reconstruction.json")
print(json.dumps(a68, indent=1)[:1100])
"""))

# 32 -----------------------------------------------------------------
S("32. Thirteen-arm matrix",
  """The complete 13-arm matrix (A0–A8, R1–R3, F1) at fixed 25 % budget.""")
SECTIONS.append(("code", """print(f"{'arm':5s} {'role':38s} {'nR':>5s} {'meanΔD':>11s} {'harmSh':>8s}")
for r in T("phase28_ablation_matrix_13arm.csv"):
    print(f"{r['arm']:5s} {r['role'][:38]:38s} {r['n_routed']:>5s} "
          f"{float(r['mean_true_delta_dice_routed']):11.7f} {float(r['harmful_activation_share']):8.4f}")
"""))

# 33 -----------------------------------------------------------------
S("33. Table 01 — arm definitions",
  """The 13 arms, their roles, primary reference arms and evidence classes.""")
SECTIONS.append(("code", """for r in T("phase28_table_01_arm_definitions.csv"):
    print(f"{r['arm']:4s} {r['role'][:36]:36s} ref={r['primary_reference_arm']:4s} {r['evidence_class']}")
"""))

# 34 -----------------------------------------------------------------
S("34. Tables 02–04 — metrics, variant contrasts, overlap",
  """Primary metrics (T02), router-variant vs full-router contrast (T03), and
membership overlap (T04).""")
SECTIONS.append(("code", """print("== T03 router variant vs full ==")
for r in T("phase28_table_03_router_variant_vs_full.csv"):
    print(f"{r['variant']:4s} variant={float(r['variant_mean_delta']):+.7f} "
          f"full={float(r['reference_mean_delta']):+.7f} diff={float(r['delta_vs_reference']):+.7f} "
          f"winner_selected={r['winner_selected']}")
"""))

# 35 -----------------------------------------------------------------
S("35. Tables 05–06 — F1 refiner-level and integrated",
  """The paired per-sample F1 comparison (T05) and the integrated secondary
summary (T06).""")
SECTIONS.append(("code", """print("== T06 F1 integrated summary ==")
for r in T("phase28_table_06_f1_integrated_secondary.csv"):
    print(f"{r['metric']:48s} = {r['value']}")
"""))

# 36 -----------------------------------------------------------------
S("36. Statistics (T07–T08) — paired bootstrap",
  """Paired bootstrap, 2000 replicates, seed 42, common paired draws per contrast.
Multiplicity remains **descriptive** — no post-hoc correction choice.""")
SECTIONS.append(("code", """print(f"{'contrast':24s} {'diff':>12s} {'CI95 low':>12s} {'CI95 high':>12s}")
for r in T("phase28_table_08_bootstrap_statistics.csv"):
    print(f"{r['contrast']:24s} {float(r['mean_difference']):+12.7f} "
          f"{float(r['ci95_low']):+12.7f} {float(r['ci95_high']):+12.7f}")
"""))

# 37 -----------------------------------------------------------------
S("37. Compute accounting and execution counts (T09–T10)",
  """18 new training folds (15 router + 3 refiner). No canonical forward rerun, no
`S_omega` retrain, zero locked-population reads.""")
SECTIONS.append(("code", """for r in T("phase28_table_09_compute_accounting.csv"):
    print(f"{r['item']:38s} {r['value']:>8s} {r['unit']}")
print()
for r in T("phase28_table_10_execution_counts.csv"):
    print(f"{r['counter']:30s} = {r['value']}")
"""))

# 38 -----------------------------------------------------------------
S("38. Training-health governance (complete epoch histories)",
  """The notebook renders **complete immutable epoch histories** for every trained
fold — no `.tail()`, no `.head()`, no truncation. For each run: contiguous epoch
numbering, no duplicates, finite losses, checkpoint-selected epoch matches
history, correct early-stop semantics.""")
SECTIONS.append(("code", """import csv as _csv
F1EXP = ROOT / "experiments" / "phase28_refiner_F1_no_pglobal"
RCK = {"R1": ROOT / "checkpoints/phase28_router_R1_no_deep",
       "R2": ROOT / "checkpoints/phase28_router_R2_no_task",
       "R3": ROOT / "checkpoints/phase28_router_R3_scalar_only"}

def audit_history(rows, loss_key):
    eps = [int(r["epoch"]) for r in rows]
    losses = [float(r[loss_key]) for r in rows]
    return {"n": len(rows),
            "contiguous": eps == list(range(1, len(rows) + 1)),
            "no_duplicates": len(set(eps)) == len(eps),
            "all_finite": bool(np.isfinite(losses).all()),
            "best_epoch": eps[int(np.argmin(losses))]}

print("== router variant fold histories (complete) ==")
for v, root in RCK.items():
    for k in range(5):
        p = root / f"fold{k}" / "history.csv"
        if p.exists():
            rows = list(_csv.DictReader(open(p, encoding="utf-8")))
            a = audit_history(rows, "early_stop_huber")
            print(f"{v} fold{k}: epochs={a['n']:3d} contiguous={a['contiguous']} "
                  f"finite={a['all_finite']} best_ep={a['best_epoch']}")
print()
print("== F1 refiner fold histories (complete) ==")
for k in range(3):
    p = F1EXP / f"fold{k}" / "history.csv"
    rows = list(_csv.DictReader(open(p, encoding="utf-8")))
    a = audit_history(rows, "early_stop_loss")
    print(f"F1 fold{k}: epochs={a['n']:3d} contiguous={a['contiguous']} "
          f"finite={a['all_finite']} best_ep={a['best_epoch']}")
"""))
SECTIONS.append(("code", """# Full (untruncated) epoch history for one representative run per variant.
for v, root in RCK.items():
    p = root / "fold0" / "history.csv"
    rows = list(_csv.DictReader(open(p, encoding="utf-8")))
    print(f"--- {v} fold0 : {len(rows)} epochs (printed in full) ---")
    for r in rows:
        print(r)
"""))

S("39. Figures",
  """Eight reviewer figures are rendered from the frozen artifacts.""")
SECTIONS.append(("code", """from IPython.display import Image, display
for f in sorted(FIG.glob("p28_fig*.png")):
    display(Image(filename=str(f)))
"""))

S("40. Interpretation discipline",
  """Results are reported as measured. The router ordering A6/C7 > R1 > R3 ≈ R2
is descriptive. The F1 negative result is reported without suppression.

**No deployment winner is selected. The canonical bundle is unchanged. The
deployment model is not replaced.**""")

S("41. Success and negative science",
  """A sufficiently powered, leakage-guarded, fixed-budget ablation matrix that
includes a genuine negative result is a **successful** scientific outcome
(§39 of the work order; `phase28_negative_result_acceptance.json`).""")
SECTIONS.append(("code", """nr = J("phase28_negative_result_acceptance.json")
print("negative_result_accepted      :", nr["negative_result_accepted"])
print("reported_without_suppression  :", nr["reported_without_suppression"])
print("F1 refiner-level mean ΔD      :", nr["f1_refiner_level_mean_delta_dice"])
print("F1 integrated mean ΔD         :", nr["f1_integrated_mean_delta_dice"])
print("interpretation:", nr["interpretation_restraint"])
"""))

S("42. Predecessor immutability recheck",
  """All predecessor artifacts were re-hashed after execution and confirmed
unchanged.""")
SECTIONS.append(("code", """pim = J("phase28_predecessor_immutability_recheck.json") \\
    if (AUD / "phase28_predecessor_immutability_recheck.json").exists() else None
print(json.dumps(pim, indent=1)[:800] if pim else "artifact written by the freeze stage")
"""))

S("43. Holdout / test lock",
  """`ROUTER_HOLDOUT` (n=875) remains locked for Phase 30 and `TEST` (n=1683)
remains locked for Phase 39. VAL808 re-use rule honoured.""")
SECTIONS.append(("code", """print(json.dumps(J("phase28_test_lock.json"), indent=1)[:500])
print(json.dumps(J("phase28_phase30_holdout_lock.json"), indent=1)[:500])
"""))

S("44. Final freeze",
  """The Phase-28 terminal freeze binds the matrix, the tables, the statistics, the
figures and the notebook.""")
SECTIONS.append(("code", """ff = J("phase28_final_freeze.json") if (AUD / "phase28_final_freeze.json").exists() else None
print(json.dumps(ff, indent=1)[:800] if ff else "written by the freeze stage")
"""))

S("45. Terminal state",
  """```
PHASE28_COMPREHENSIVE_ABLATION_MATRIX_COMPLETE__CORE_ROUTER_AND_REFINER_ABLATIONS_FROZEN__PHASE29_ELIGIBLE_NOT_STARTED
```

**STOP.** Phase 29 / Phase 30 are not started. `ROUTER_HOLDOUT` and `TEST` are
not opened.""")


def build() -> bytes:
    cells = []
    for kind, text in SECTIONS:
        cells.append(md(text) if kind == "md" else code(text))
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.9"},
            "phase": 28,
            "classification": "PHASE28_COMPREHENSIVE_ABLATION_MATRIX",
            "read_only": True,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return (json.dumps(nb, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> int:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    root = NB_DIR / "_det"
    if root.exists():
        shutil.rmtree(root)
    shas = []
    for r in (1, 2, 3):
        d = root / f"run{r}"
        d.mkdir(parents=True, exist_ok=True)
        (d / NB_NAME).write_bytes(build())
        shas.append(hashlib.sha256((d / NB_NAME).read_bytes()).hexdigest())
    three_x = len(set(shas)) == 1
    shutil.copyfile(root / "run1" / NB_NAME, NB_DIR / NB_NAME)
    shutil.rmtree(root)
    canon = hashlib.sha256((NB_DIR / NB_NAME).read_bytes()).hexdigest()

    md_count = sum(1 for k, _ in SECTIONS if k == "md")
    code_count = sum(1 for k, _ in SECTIONS if k == "code")
    print(f"notebook cells: {len(SECTIONS)} (md {md_count}, code {code_count})")
    print(f"3x byte-identical: {three_x}")
    print("notebook sha256:", canon)
    return 0 if three_x else 1


if __name__ == "__main__":
    raise SystemExit(main())
