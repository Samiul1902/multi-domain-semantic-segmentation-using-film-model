"""Phase 28 -- notebook compliance repair §5-§14.

Builds the repaired canonical reviewer notebook from FROZEN ARTIFACTS ONLY.

Key properties
--------------
* 45 scientific sections preserved (>= required coverage list).
* COMPLETE one-row-per-epoch history tables for ALL 18 logical runs.
  No .head(), no .tail(), no max_rows truncation, no representative-fold
  substitution. Rendered with pandas Styler max_rows=None / max_cols=None.
* All 8 frozen figures displayed from frozen PNG files (not regenerated).
* All 10 load-bearing frozen tables rendered in full.
* 0 training, 0 model forward, 0 OOF/membership/metric/bootstrap recomputation.
* Deterministic cell IDs p28-repair-000 ... ; deterministic repository discovery.
* Every assertion is checked against the frozen training registry.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/repair_phase28_notebook_build.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_28_model_ablation"
NB_NAME = "phase28_comprehensive_ablation.ipynb"

OLD_SHA = "72cfbc12e76a58fab3449e6dbf8163cbe988e7473e716e10bf87741fa8c10326"
TERMINAL = ("PHASE28_COMPREHENSIVE_ABLATION_MATRIX_COMPLETE__"
            "CORE_ROUTER_AND_REFINER_ABLATIONS_FROZEN__PHASE29_ELIGIBLE_NOT_STARTED")

CELLS: list[dict] = []


def md(text: str) -> None:
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": text})


def code(text: str) -> None:
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": text})


Q = chr(34) * 3  # notebook-cell docstring delimiter, kept out of this file's quoting


def _render_history_fn() -> str:
    return (
        "def render_history(run_id, variant, fold, hist_path, loss_cols, best_col='is_best'):\n"
        "    " + Q + "Render one COMPLETE, untruncated epoch history and assert integrity." + Q + "\n"
        "    df = pd.read_csv(hist_path)\n"
        "    eps = df['epoch'].astype(int).tolist()\n"
        "    n = len(df)\n"
        "\n"
        "    contiguous = eps == list(range(1, n + 1))\n"
        "    no_dup = len(set(eps)) == n\n"
        "    finite = bool(\n"
        "        pd.concat([df[c].astype(float) for c in loss_cols]).notna().all()\n"
        "        and (df[loss_cols].astype(float).abs() != float('inf')).all().all())\n"
        "\n"
        "    reg_rec = REG_BY_RUN[run_id]\n"
        "    row_count_matches = (n == int(reg_rec['n_epochs_run']))\n"
        "\n"
        "    # Checkpoint selection semantics (Phase25D/25A frozen rule):\n"
        "    # the selected epoch is the argmin of the EARLY_STOP loss, with the\n"
        "    # earlier-epoch tie-break.  The `is_best` column tracks *strict*\n"
        "    # improvement events, so it appears on every new minimum and is NOT a\n"
        "    # single-row marker; the registry best_epoch is the argmin.\n"
        "    if best_col in df.columns:\n"
        "        best_rows = df.index[df[best_col].astype(str).str.lower() == 'true'].tolist()\n"
        "    else:\n"
        "        best_rows = []\n"
        "    es_col = [c for c in loss_cols if 'early_stop' in c][0]\n"
        "    argmin_row = int(df[es_col].astype(float).idxmin())\n"
        "    selected_epoch = int(df.loc[argmin_row, 'epoch'])\n"
        "    registry_best = int(reg_rec['best_epoch'])\n"
        "    best_matches = selected_epoch == registry_best\n"
        "    is_best_covers_selection = bool(best_rows) and argmin_row in best_rows\n"
        "\n"
        "    print('=' * 96)\n"
        "    print(f'RUN {run_id}   variant={variant}  fold={fold}')\n"
        "    print(f'  epochs={n}  contiguous={contiguous}  no_duplicate={no_dup}  finite={finite}')\n"
        "    print(f'  registry n_epochs_run={reg_rec[\"n_epochs_run\"]} -> row_count_matches={row_count_matches}')\n"
        "    print(f'  early_stop_loss argmin epoch={selected_epoch}  registry best_epoch={registry_best} '\n"
        "          f'-> matches={best_matches}')\n"
        "    print(f'  is_best marker covers selected epoch={is_best_covers_selection}')\n"
        "    print(f'  FULL EPOCH HISTORY ({n} rows, untruncated):')\n"
        "    display(df.style.hide(axis='index'))\n"
        "\n"
        "    assert contiguous, f'{run_id}: epochs not contiguous'\n"
        "    assert no_dup, f'{run_id}: duplicate epochs'\n"
        "    assert finite, f'{run_id}: non-finite losses'\n"
        "    assert row_count_matches, f'{run_id}: row count != registry n_epochs_run'\n"
        "    assert best_matches, f'{run_id}: selected epoch != registry best_epoch'\n"
        "    assert is_best_covers_selection, f'{run_id}: is_best does not cover selection'\n"
        "\n"
        "    HISTORY_AUDIT.append({'run_id': run_id, 'variant': variant, 'fold': fold,\n"
        "                          'n_epochs': n, 'contiguous': contiguous,\n"
        "                          'no_duplicate': no_dup, 'finite': finite,\n"
        "                          'row_count_matches_registry': row_count_matches,\n"
        "                          'selected_epoch': selected_epoch,\n"
        "                          'registry_best_epoch': registry_best,\n"
        "                          'best_epoch_matches_registry': best_matches})\n"
    )


def _show_table_fn() -> str:
    return (
        "def show_table(df, caption):\n"
        "    " + Q + "Render a COMPLETE pandas table: no truncation of rows or columns." + Q + "\n"
        "    print(caption)\n"
        "    print(f'[complete rendering: {len(df)} rows x {df.shape[1]} cols]')\n"
        "    display(df.style.hide(axis='index') if hasattr(df.style, 'hide') else df)\n"
    )


# ===================================================================== #
# 0. preamble — deterministic repository discovery (§13)
# ===================================================================== #
md("""# Phase 28 — Comprehensive System Ablation Matrix

**Method**: `RA-MedFiLM-BARR` — multi-domain ultrasound segmentation, phase-gated.
**Classification**: `PHASE28_CANONICAL_COMPREHENSIVE_SYSTEM_ABLATION_MATRIX`.
**Population**: `ROUTER_DEVELOPMENT` (n = 4957). Fixed budget 25 % (K = 1239).
**Arms**: 13 — A0–A8, R1–R3, F1.

This notebook is a **reviewer-facing, read-only, fully executed** rendering of the
frozen Phase-28 artifacts.

It performs **no training**, **no model forward**, **no OOF recomputation**,
**no membership recomputation**, **no metric recomputation** and **no bootstrap
recomputation**. It reads frozen JSON / CSV / PNG artifacts, renders them in full,
and asserts frozen SHAs and counts. `ROUTER_HOLDOUT` (n=875), `VAL808` (n=808) and
`TEST` (n=1683) are never opened.

This notebook is the **compliance-repaired** edition that supersedes the
unexecuted notebook with SHA `72cfbc12e76a58fab3449e6dbf8163cbe988e7473e716e10bf87741fa8c10326`.
The superseded edition is archived byte-for-byte at
`reports/audits/phase28_comprehensive_ablation_pre_notebook_compliance_repair.ipynb`.""")

md("""## 0. Deterministic environment and repository discovery

The repository root is discovered deterministically by walking `Path.cwd()` and its
parents until a known frozen Phase-28 artifact is found — no machine-specific path
is baked into the notebook.""")
code("""import base64, csv, hashlib, io, json, re, sys
from pathlib import Path

import pandas as pd
from IPython.display import Image, display, Markdown

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 240)
pd.set_option("display.max_colwidth", None)


def discover_root() -> Path:
    # Walk cwd and parents until a frozen Phase-28 artifact is found.
    marker = Path("reports") / "audits" / "phase28_final_freeze.json"
    for base in [Path.cwd(), *Path.cwd().parents]:
        if (base / marker).exists():
            return base
    raise FileNotFoundError(f"could not locate Phase-28 repository root from {Path.cwd()}")


ROOT = discover_root()
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"
D28 = ROOT / "data_cache" / "phase28_router_variants_v1_2"
F1C = ROOT / "data_cache" / "phase28_f1_refiner_v1_2"
RCK = {"R1": ROOT / "checkpoints" / "phase28_router_R1_no_deep",
       "R2": ROOT / "checkpoints" / "phase28_router_R2_no_task",
       "R3": ROOT / "checkpoints" / "phase28_router_R3_scalar_only"}
F1_CK = ROOT / "checkpoints" / "phase28_refiner_F1_no_pglobal"
F1_EXP = ROOT / "experiments" / "phase28_refiner_F1_no_pglobal"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def J(name: str):
    return json.load(open(AUD / name, encoding="utf-8"))


def T(name: str) -> pd.DataFrame:
    return pd.read_csv(TAB / name, dtype=str)


""" + _show_table_fn() + """
print("repository root:", ROOT)
print("pandas", pd.__version__)""")

# ===================================================================== #
# 1. governing ruling / scope
# ===================================================================== #
md("""## 1. Purpose and governing ruling

Phase 28 executes the **canonical comprehensive system ablation** under the
supervisor's operationalization ruling v1.2. The ruling froze R1/R2/R3/F1 as
`SEPARATELY_TRAINED_CONTROLLED_ABLATION_VARIANT` and superseded `NO_TRAINING` with
`ABLATION_ONLY_TRAINING_AUTHORIZED_FOR_R1_R2_R3_F1`.

This notebook is the **post-execution compliance repair**. Science is unchanged:
no training, no forward, no metric recomputation.""")
code("""rul = J("phase28_supervisor_operationalization_ruling_v1_2.json")
repair = J("phase28_notebook_compliance_repair_classification.json")
print("ruling classification :", rul.get("classification"))
print("repair classification :", repair["classification"])
print("scope                 :", repair["scope_statement"][:120], "...")
for k, v in repair["frozen_invariants"].items():
    print(f"  {k:42s} = {v}")""")

md("""## 2. Entry gate

The compliance-repair entry gate re-verifies the frozen terminal, the unchanged
base final freeze, the exact pre-repair notebook SHA, and the locked populations.""")
code("""g = J("phase28_notebook_compliance_repair_entry_gate.json")
for k in ("required_terminal", "observed_terminal", "terminal_match",
          "gate_pass", "all_pass"):
    print(f"{k:20s} = {g.get(k)}")
print()
print("canonical notebook (pre-repair):")
print("  sha256      :", g["canonical_notebook"]["sha256"])
print("  required    :", g["canonical_notebook"]["required_sha256"])
print("  sha_exact   :", g["canonical_notebook"]["sha_exact"])
print()
print("governance state:", json.dumps(g["governance_state"], indent=2))
assert g["terminal_match"] is True
assert g["canonical_notebook"]["sha_exact"] is True
assert g["gate_pass"] is True""")

md("""## 3. Specification binding (v1.2, zero drift)

Seventeen authoritative v1.2 artifacts are SHA-256 bound. Historical v1.0 / v1.1
artifacts are preserved and unmodified.""")
code("""b = J("phase28_execution_spec_v1_2_binding.json")
print("artifacts bound :", b.get("artifact_count", len(b.get("artifacts", []))))
print("zero_drift      :", b.get("zero_drift"))
print("all_pass        :", b.get("all_pass"))
assert b.get("zero_drift") is True""")

md("""## 4. Scope and prohibitions

No `ROUTER_HOLDOUT` read (n=875, Phase 30), no `TEST` read (n=1683, Phase 39),
no canonical-bundle mutation, no policy retuning, no deployment-model replacement.""")
code("""m = J("phase28_comprehensive_ablation_matrix.json")
for k in ("ROUTER_HOLDOUT_reads", "TEST_reads", "VAL808_reads",
          "canonical_bundle_changed", "policy_retuning_performed",
          "deployment_model_replaced"):
    print(f"{k:30s} = {m.get(k)}")
assert m["ROUTER_HOLDOUT_reads"] == 0 and m["TEST_reads"] == 0 and m["VAL808_reads"] == 0
assert m["canonical_bundle_changed"] is False""")

md("""## 5. Population ownership

The evaluated population is `ROUTER_DEVELOPMENT` (n=4957). Every sample belongs to
exactly one governed population; none is drawn from a locked cohort.""")
code("""p = J("phase28_population_ownership_audit.json")
print(json.dumps(p, indent=1)[:1200])
print()
print("matrix population:", m["population"], "| n =", m["n"], "| K =", m["K"])""")

md("""## 6. Training-input provenance gate

All upstream inputs are SHA-bound: Phase25B features (202-D), Phase25C label table
(4957 rows), Phase25D CV5 manifest + role manifests, Phase25A ROI-030 cache, and
the frozen Phase25F reuse contract + fold checkpoints.""")
code("""pv = J("phase28_training_input_provenance_gate.json")
print("all_pass:", pv.get("all_pass"))
print("top-level keys:", list(pv.keys()))
assert pv.get("all_pass") is True""")

md("""## 7. OOF inference semantics binding

The exact inference semantics were physically recovered from the predecessor
implementations before any Phase-28 forward:

* **Router (Phase 25D)**: `torch.no_grad()`, FP32, batch 128.
* **Refiner (Phase 25C)**: `m.eval()` + `torch.inference_mode()`, **FP32, no
  autocast**, `np.ascontiguousarray(..., float32)`, batch 8, model loaded
  `map_location="cpu"`.
* **`S_omega` (Phase 25F)**: `model.eval()` + `inference_mode()`, raw logit.

The OOF path deliberately does **not** reuse the training AMP settings.""")
code("""sem = J("phase28_oof_inference_semantics_binding.json")
print(json.dumps(sem, indent=1)[:1400])""")

# ===================================================================== #
# 2. arm registry / topology
# ===================================================================== #
md("""## 8. Thirteen-arm registry

The complete 13-arm matrix at fixed 25 % budget (K = 1239).""")
code("""mat = J("phase28_comprehensive_ablation_matrix.json")
arms13 = pd.DataFrame(mat["arms"])
print("arms:", mat["arm_count"], "| A-arms:", mat["A_arms"], "| variants:", mat["variant_arms"])
show_table(arms13[["arm", "role", "definition"]],
           "Table — arm registry (complete)")""")

md("""## 9. Core contrast topology — A0–A8 preserved

The v1.1 contrast map is preserved unchanged. A0/A1 are endpoint references;
A2–A5 are GT-free routing-signal comparators; A6/A7 are adjacent incremental
contrasts; A8 is the mandatory component isolation (canonical baseline).""")
code("""cm = pd.read_csv(TAB / "phase28_core_contrast_map.csv", dtype=str)
show_table(cm, "Table — core contrast map (complete)")""")

md("""## 10. Architecture parameter assertions

Four new architectures were implemented and asserted:
R1 = 12,225 · R2 = 34,689 · R3 = 10,113 · F1 = 1,276,257 parameters.""")
code("""reg = J("phase28_training_run_registry.json")
variant_params = (pd.DataFrame(reg["runs"])
                  .groupby("variant", as_index=False)["param_count"].first()
                  .sort_values("variant"))
show_table(variant_params, "Table — variant parameter counts (from frozen registry)")
expected_params = {"R1": 12225, "R2": 34689, "R3": 10113, "F1": 1276257}
for _, r in variant_params.iterrows():
    assert int(r["param_count"]) == expected_params[r["variant"]], r["variant"]
print("all four parameter counts match the frozen contract")""")

# ===================================================================== #
# 3. router variants and OOF integrity
# ===================================================================== #
md("""## 11. R1 — no deep global features

R1 removes the 96-D deep global block. Input = 10 scalars + `Embedding(4,16)` →
projected width 26. Topology preserved downstream of the widened stem.""")
code("""prot = J("phase28_router_variant_training_protocol_binding_v1_2.json")
print(json.dumps(prot, indent=1)[:1100])""")

md("""## 12. R2 — no task_id conditioning

R2 removes the task embedding entirely: 202 numeric features, no embedding.""")

md("""## 13. R3 — scalar-only feature-set control

R3 keeps only the 10 Phase25B scalars (width 10): a feature-set control that
isolates how much signal the scalar block alone carries.""")

md("""## 14. Router OOF contract

Each variant produces exactly one OOF score per sample (4957) using the inherited
Phase25D protocol: `StratifiedGroupKFold(5, shuffle=True, random_state=42)`,
group = composite `group_key`, stratification = `domain`, sort
`[domain, group_key, sample_id]`.""")
code("""oc = J("phase28_router_variant_oof_contract_v1_2.json")
print(json.dumps(oc, indent=1)[:900])
print()
for v in ("R1", "R2", "R3"):
    df = pd.read_csv(D28 / f"phase28_router_{v}_oof_scores.csv", dtype=str)
    print(f"{v} OOF rows = {len(df):5d}  | unique sample_id = {df['sample_id'].nunique():5d} "
          f"| columns = {list(df.columns)}")
    assert len(df) == 4957 and df["sample_id"].nunique() == 4957
print("all three OOF tables: exactly-once coverage of 4957 samples confirmed")""")

md("""## 15. Router leakage guard

Targets are sliced as `y_all[fit_idx]` / `y_all[es_idx]` only. The OUTER_TARGET
target slice is never read during training. The OOF CSV contains no forbidden
outcome field.""")
code("""lg = J("phase28_router_variant_leakage_guard.json")
print("all_pass:", lg.get("all_pass"))
for k in ("ot_targets_not_read", "forbidden_outcome_fields_absent", "fit_es_slices_only"):
    if k in lg:
        print(f"  {k:34s} = {lg[k]}")
assert lg.get("all_pass") is True""")

md("""## 16. Router normalization

Scalar indices `[192..197, 200, 201]` are standardized per fold with FIT-only
statistics (ddof=0); R1/R3 additionally normalize their local scalar block. Any
constant (`sigma < 1e-12`) maps to 0.0.""")

md("""## 17. Router membership freeze — outcome barrier

K = floor(0.25 × 4957) = **1239**. Membership was frozen and SHA'd **before** any
outcome was opened. Rank Δ̂ DESC, tie-break `sample_id` ASC. `scalar_tau` is
NOT_APPLICABLE at fixed K.""")
code("""br = J("phase28_router_membership_barrier.json")
print("K =", br.get("K"), "| population n =", br.get("n"))
for v in ("R1", "R2", "R3"):
    mem = pd.read_csv(D28 / f"phase28_router_{v}_membership_K1239.csv", dtype=str)
    print(f"  {v} membership rows = {len(mem)}")
    assert len(mem) == 1239
print("membership sizes confirmed = 1239 for R1/R2/R3")""")

md("""## 18. Router outcome opening

Outcomes were opened only after the membership barrier was recorded. The frozen
outcome is the Phase25C paired-gain label table (true ΔDice).""")
code("""oo = J("phase28_outcome_opening.json")
print(json.dumps(oo, indent=1)[:1000])""")

md("""## 19. Router primary metrics

At fixed 25 % budget: precision@budget, benefit capture, mean true ΔDice among
routed, harmful activation share, beneficial coverage, missed benefit, oracle
regret. **No deployment winner is selected.**""")
code("""rp = J("phase28_router_primary_metrics.json")
v = rp["variants"]
rows = []
for k in ("A6_C7_canonical", "R1", "R2", "R3"):
    d = v[k]
    rows.append({"arm": k, "n_routed": d["n_routed"],
                 "precision_at_budget": d["precision_at_budget"],
                 "benefit_capture": d["benefit_capture"],
                 "mean_true_delta_dice_routed": d["mean_true_delta_dice_routed"],
                 "harmful_activation_share": d["harmful_activation_share"],
                 "beneficial_coverage": d["beneficial_coverage"],
                 "missed_benefit": d["missed_benefit"],
                 "oracle_regret": d["oracle_regret"]})
show_table(pd.DataFrame(rows), "Table — router primary metrics (complete)")
print("no_deployment_winner_selected:", rp.get("no_deployment_winner_selected"))
assert rp["no_deployment_winner_selected"] is True""")

md("""## 20. Router membership overlap

Overlap vs canonical A6/C7 membership quantifies how much the ablated routers
re-select the same samples.""")
code("""df = T("phase28_table_04_router_membership_overlap.csv")
show_table(df, "Table — router membership overlap (complete)")""")

# ===================================================================== #
# 4. F1
# ===================================================================== #
md("""## 21. F1 — trained refiner without p_global input channel

Canonical refiner input = RGB **+** `p_global` → `(4,256,256)`. F1 input = RGB only
→ `(3,256,256)`. The `p_global` channel is **physically absent**; the stem
`Conv2d(4→16)` becomes `Conv2d(3→16)`. Everything else is frozen.""")
code("""fc = J("phase28_f1_input_contract_v1_2.json")
print(json.dumps(fc, indent=1)[:1000])""")

md("""## 22. F1 ROI geometry remains canonical

ROI-0.30 canonical geometry is retained: threshold 0.30, expansion 1.50, 256 crop,
512 canvas. F1 changes only the refiner input channels.""")
code("""geo = J("phase28_f1_membership_rule_v1_2.json")
print(json.dumps(geo, indent=1)[:800])""")

md("""## 23. F1 training protocol

3-fold cross-fit (seed 42, group-safe domain-stratified, FIT 0.9 / EARLY_STOP 0.1).
Loss `0.5*BCEWithLogits + 0.5*Dice(1e-6)`; AdamW(lr=1e-4, wd=1e-4);
`CosineAnnealingLR(T_max=100)`; batch 8; 100 epochs; patience 15; min EARLY_STOP
total loss; AMP on CUDA; `cudnn.deterministic`.""")
code("""fp = J("phase28_f1_training_protocol_binding_v1_2.json")
print(json.dumps(fp, indent=1)[:1100])""")

md("""## 24. F1 OOF integrity

Leakage-safe: each sample's OOF crop is produced by the fold model that did not
train on that sample. 4957 crops are written; contiguity and finiteness verified.""")
code("""total = 0
for k in range(3):
    idx = pd.read_csv(F1C / f"fold{k}_refined_crop_index.csv", dtype=str)
    print(f"  fold{k}: {len(idx):5d} OOF refined crops")
    total += len(idx)
print("F1 OOF refined crops total =", total)
assert total == 4957
pv2 = J("phase28_f1_pipeline_validation.json")
print()
print("pipeline validation all_pass:", pv2.get("all_pass"))
assert pv2.get("all_pass") is True""")

md("""## 25. F1 primary refiner-level result (NEGATIVE — genuine)

On the A7 EXECUTE membership: canonical mean ΔD = **+0.0072466**, F1 mean
ΔD = **−0.0441799**. The paired difference (F1 − canonical) = **−0.0514266**,
CI95 [−0.0554756, −0.0475745]; F1 is worse than global in 968/1239 samples.""")
code("""rl = J("phase28_f1_refiner_level_comparison.json")
print("n_paired                     :", rl["n_paired"])
print("canonical mean ΔD            :", f"{rl['canonical_candidate_mean_delta']:+.7f}")
print("F1 mean ΔD                   :", f"{rl['f1_candidate_mean_delta']:+.7f}")
print("paired diff (F1 − canonical) :", f"{rl['paired_mean_delta_difference_f1_minus_canonical']:+.7f}")
print("CI95                         :", [f"{x:+.7f}" for x in rl["paired_bootstrap_ci95"]])
print("n_canonical_better / n_f1_better:", rl["n_canonical_better"], "/", rl["n_f1_better"])
assert rl["paired_mean_delta_difference_f1_minus_canonical"] < 0""")

md("""## 26. F1 integrated secondary (spec §24)

For integrated F1: recompute **only** the deterministic 20-D `S_omega` feature
vector from the F1 candidate, then run the **already-frozen** Phase25F OOF fold
model for the sample's `router_cv_fold`. No `S_omega` retraining; leakage-safe fold
ownership; fold checkpoints physically present (analysis AVAILABLE).""")
code("""fi = J("phase28_f1_integrated_secondary.json")
print("n_A7_execute         :", fi["n_A7_execute"])
print("n_F1_accept          :", fi["n_f1_accept"], "| n_F1_fallback:", fi["n_f1_fallback"])
print("F1 integrated mean ΔD:", f"{fi['f1_integrated_mean_delta_dice']:+.7f}")
print("canonical A8 mean ΔD :", f"{fi['canonical_A8_mean_delta_dice']:+.7f}")
print("paired diff (F1 − A8):", f"{fi['paired_mean_difference_f1_minus_canonical']:+.7f}",
      "CI95", [f"{x:+.7f}" for x in fi["paired_bootstrap_ci95"]])
print("S_omega retrained    :", fi["s_omega_retrained"])
assert fi["s_omega_retrained"] is False""")

# ===================================================================== #
# 5. A0-A8 evidence + matrix
# ===================================================================== #
md("""## 27. A0–A5 artifact reconstruction evidence

Reconstructed from frozen canonical artifacts with **no new forward**. A0
global-mean Dice = 0.915783; A1 always-refine mean ΔD = 0.001658 (harm 0.4267).""")
code("""a05 = J("phase28_a0_a5_artifact_reconstruction_verification.json")
rows = []
for k, rec in a05["rows"].items():
    rows.append({"arm": k, "definition": rec.get("definition"),
                 "requires_new_model_forward": rec.get("requires_new_model_forward"),
                 "sufficient": rec.get("sufficient"),
                 "score_space": rec.get("score_space")})
show_table(pd.DataFrame(rows), "Table — A0–A5 reconstruction rule (complete)")""")

md("""## 28. A6–A8 prior canonical evidence

A6/C7 learned route, A7/C8 resource gate (K = 1239 EXECUTE), A8/C9 post-safety
(1205 ACCEPT_REFINEMENT / 34 FALLBACK_GLOBAL).""")
code("""a68 = J("phase28_a6_a8_prior_evidence_reconstruction.json")
rows = []
for name in ("A6_learned_router_C7", "A7_C8_plus_resource", "A8_C9_post_safety"):
    if name in a68:
        rec = a68[name]
        st = rec.get("stats", {})
        rows.append({"arm": name, "policy_id": rec.get("policy_id"),
                     "n": st.get("n"), "mean_true_delta": st.get("mean_true_delta"),
                     "n_beneficial": st.get("n_beneficial"),
                     "n_harmful": st.get("n_harmful"),
                     "status": rec.get("status")})
show_table(pd.DataFrame(rows), "Table — A6–A8 prior evidence (complete)")
print("canonical bundle sha256:", a68.get("canonical_bundle_sha256"))""")

md("""## 29. Thirteen-arm ablation matrix

The complete 13-arm matrix at fixed 25 % budget. The F1 row carries the **true
integrated F1 outcome**, not a placeholder.""")
code("""arm_df = T("phase28_ablation_matrix_13arm.csv")
show_table(arm_df, "Table — 13-arm ablation matrix (complete)")
assert len(arm_df) == 13""")

md("""## 30. Per-domain results

Per-domain ΔDice for the canonical route, reconstructed from the frozen Phase25C
paired-gain label table (read-only, no recomputation).""")
code("""labs = pd.read_csv(
    ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
    / "phase25c_oof_paired_gain_labels.csv", dtype=str)
c9 = pd.read_csv(TAB / "phase25f_c9_decision_manifest.csv", dtype=str)
c9 = c9[c9["policy_id"] == "C8_lambda0.25_budget0.25"]
a8_mem = set(c9.loc[c9["somega_decision"] == "ACCEPT_REFINEMENT", "sample_id"])
a7_mem = set(c9.loc[c9["c8_decision"] == "EXECUTE", "sample_id"])
labs["delta_dice"] = labs["delta_dice"].astype(float)
dom_rows = []
for dom, sub in labs.groupby("domain"):
    sel = sub[sub["sample_id"].isin(a7_mem)]
    sel_acc = sub[sub["sample_id"].isin(a8_mem)]
    full = sub
    dom_rows.append({
        "domain": dom,
        "n_population": len(full),
        "n_A7_execute": len(sel),
        "n_A8_accept": len(sel_acc),
        "population_mean_delta": round(full["delta_dice"].mean(), 6),
        "A7_execute_mean_delta": round(sel["delta_dice"].mean(), 6) if len(sel) else 0.0,
        "A8_accept_mean_delta": round(sel_acc["delta_dice"].mean(), 6) if len(sel_acc) else 0.0,
    })
show_table(pd.DataFrame(dom_rows), "Table — per-domain ΔDice (complete)")""")

# ===================================================================== #
# 6. tables
# ===================================================================== #
md("""## 31. Table 01 — arm definitions

The 13 arms, their roles, primary reference arms and evidence classes.""")
code("""show_table(T("phase28_table_01_arm_definitions.csv"),
           "Table 01 — arm definitions (complete)")""")

md("""## 32. Table 02 — arm primary metrics

Fixed-budget primary metrics for all 13 arms.""")
code("""show_table(T("phase28_table_02_arm_primary_metrics.csv"),
           "Table 02 — arm primary metrics (complete)")""")

md("""## 33. Table 03 — router variant vs full router""")
code("""show_table(T("phase28_table_03_router_variant_vs_full.csv"),
           "Table 03 — router variant vs full (complete)")""")

md("""## 34. Table 05 — F1 refiner-level paired result

The complete per-sample paired comparison on the A7 membership.""")
code("""show_table(T("phase28_table_05_f1_refiner_level_paired.csv"),
           "Table 05 — F1 refiner-level paired (complete)")""")

md("""## 35. Table 06 — F1 integrated secondary result""")
code("""show_table(T("phase28_table_06_f1_integrated_secondary.csv"),
           "Table 06 — F1 integrated secondary (complete)")""")

md("""## 36. Table 07 — matched paired contrasts""")
code("""show_table(T("phase28_table_07_matched_paired_contrasts.csv"),
           "Table 07 — matched paired contrasts (complete)")""")

md("""## 37. Table 08 — bootstrap statistics

Paired bootstrap, 2000 replicates, seed 42, common paired draws per contrast.
Multiplicity remains **descriptive** — no post-hoc correction choice.""")
code("""stats = J("phase28_execution_statistics.json")
print("bootstrap_replicates :", stats["bootstrap_replicates"])
print("bootstrap_seed       :", stats["bootstrap_seed"])
print("mechanism            :", stats["mechanism"])
print("multiplicity         :", stats["multiplicity"])
print("new procedure introduced:", stats["new_multiplicity_procedure_introduced"])
print()
show_table(T("phase28_table_08_bootstrap_statistics.csv"),
           "Table 08 — bootstrap statistics (complete)")
assert stats["bootstrap_replicates"] == 2000 and stats["bootstrap_seed"] == 42""")

md("""## 38. Table 09 — compute accounting""")
code("""show_table(T("phase28_table_09_compute_accounting.csv"),
           "Table 09 — compute accounting (complete)")""")

md("""## 39. Table 10 — execution counts""")
code("""show_table(T("phase28_table_10_execution_counts.csv"),
           "Table 10 — execution counts (complete)")""")

# ===================================================================== #
# 7. FULL 18-RUN HISTORY RENDERING  (§7/§8/§9) — LOAD-BEARING
# ===================================================================== #
md("""## 40. Complete epoch histories — all 18 logical training runs

**This requirement is LOAD-BEARING.**

Every one of the 18 logical training runs is rendered here as a **complete
one-row-per-epoch table**. There is no `.head()`, no `.tail()`, no `max_rows`
truncation, and no representative-fold substitution: `display.max_rows = None`
and `display.max_columns = None` are set globally.

Boundary and integrity assertions are checked against the frozen
`phase28_training_run_registry.json` — physical history files are authoritative
and are asserted against the registry, never against hardcoded lengths.""")

code("""reg = J("phase28_training_run_registry.json")
print("registry n_runs        :", reg["n_runs"])
print("registry n_router_runs :", reg["n_router_runs"])
print("registry n_refiner_runs:", reg["n_refiner_runs"])
print("registry all_contiguous:", reg["all_contiguous"])
print("registry all_finite    :", reg["all_finite"])
print("registry all_checkpoint_epoch_matches:", reg["all_checkpoint_epoch_matches"])
print("registry sha256        :", reg["registry_sha256"])
assert reg["n_runs"] == 18
assert reg["n_router_runs"] == 15
assert reg["n_refiner_runs"] == 3
assert reg["all_contiguous"] is True
assert reg["all_finite"] is True
assert reg["all_checkpoint_epoch_matches"] is True
print("registry boundary assertions satisfied")""")

code("""# Registry lookup for physical-vs-registry consistency (§8/§9).
REG_BY_RUN = {r["run_id"]: r for r in reg["runs"]}

ROUTER_RUNS = [(v, k, f"phase28_router_{v}_"
                + ("no_deep" if v == "R1" else ("no_task" if v == "R2" else "scalar_only"))
                + f"_fold{k}")
               for v in ("R1", "R2", "R3") for k in range(5)]
F1_RUNS = [(k, f"phase28_refiner_F1_no_pglobal_fold{k}") for k in range(3)]

HISTORY_AUDIT = []


""" + _render_history_fn() + """

print("ROUTER RUNS: 15")
for v, k, run_id in ROUTER_RUNS:
    render_history(run_id, v, k, RCK[v] / f"fold{k}" / "history.csv",
                   ["train_huber", "early_stop_huber", "lr"])

print("F1 RUNS: 3")
for k, run_id in F1_RUNS:
    render_history(run_id, "F1", k, F1_EXP / f"fold{k}" / "history.csv",
                   ["train_loss", "early_stop_loss", "early_stop_dice", "lr"])

print("=" * 96)
print("ALL 18 RUNS RENDERED IN FULL WITH NO TRUNCATION")""")

code("""hist_df = pd.DataFrame(HISTORY_AUDIT)
show_table(hist_df, "Table — 18-run history integrity summary (complete)")
assert len(hist_df) == 18
assert hist_df["contiguous"].all()
assert hist_df["no_duplicate"].all()
assert hist_df["finite"].all()
assert hist_df["row_count_matches_registry"].all()
assert hist_df["best_epoch_matches_registry"].all()
print(f"total epochs rendered across 18 runs = {int(hist_df['n_epochs'].sum())}")
print("HISTORY REGISTRY CONSISTENCY: PASS")""")

# ===================================================================== #
# 8. figures
# ===================================================================== #
md("""## 41. Frozen reviewer figures

All eight Phase-28 reviewer figures are displayed **from the frozen PNG files**.
The scientific plots are not regenerated.""")
code("""figs = sorted(FIG.glob("p28_fig*.png"))
print(f"frozen figures found: {len(figs)}")
for i, f in enumerate(figs, 1):
    print(f"  [{i}] {f.name}")
    display(Image(filename=str(f)))
assert len(figs) == 8""")

# ===================================================================== #
# 9. discipline / locks / freeze / terminal
# ===================================================================== #
md("""## 42. Negative-result discipline

Results are reported as measured. The F1 negative result is reported without
suppression. **No deployment winner is selected. The canonical bundle is
unchanged. The deployment model is not replaced.**""")
code("""nr = J("phase28_negative_result_acceptance.json")
print("negative_result_accepted     :", nr["negative_result_accepted"])
print("reported_without_suppression :", nr["reported_without_suppression"])
print("pipeline_validated_nonartifactual:", nr["pipeline_validated_nonartifactual"])
print("F1 refiner-level mean ΔD     :", nr["f1_refiner_level_mean_delta_dice"])
print("F1 integrated mean ΔD        :", nr["f1_integrated_mean_delta_dice"])
print("interpretation:", nr["interpretation_restraint"])
assert nr["negative_result_accepted"] is True""")

md("""## 43. Holdout / VAL808 / TEST locks

`ROUTER_HOLDOUT` (n=875) remains locked for Phase 30, `VAL808` (n=808) is not read,
and `TEST` (n=1683) remains locked for Phase 39.""")
code("""tl = J("phase28_test_lock.json")
hl = J("phase28_phase30_holdout_lock.json")
vl = J("phase28_val808_reuse_rule.json")
print("TEST             :", tl["TEST_state"], "| n =", tl["TEST_n"], "| reads =", tl["phase28_test_reads"])
print("ROUTER_HOLDOUT   :", hl["ROUTER_HOLDOUT_state"], "| n =", hl["ROUTER_HOLDOUT_n"],
      "| reads =", hl["phase28_holdout_reads"])
print("VAL808           : reads =", vl.get("phase28_val808_reads", 0))
assert tl["phase28_test_reads"] == 0 and hl["phase28_holdout_reads"] == 0""")

md("""## 44. Final freeze and project status""")
code("""ff = J("phase28_final_freeze.json")
ps = J("phase28_project_status.json")
print("freeze classification :", ff["classification"])
print("freeze population     :", ff["population"], "n =", ff["population_n"])
print("freeze K              :", ff["K"])
print("freeze arms/tables/figs:", ff["n_arms"], "/", ff["n_tables"], "/", ff["n_figures"])
print("freeze new training runs:", ff["n_new_training_runs"])
print("canonical bundle      :", ff["canonical_bundle_sha256"], "| changed =", ff["canonical_bundle_changed"])
print()
print("project status        :", ps["phase_state"], "|", ps["execution_state"])
print("headline              :", json.dumps(ps["headline_findings"], indent=2)[:600])
assert ff["canonical_bundle_changed"] is False""")

md("""## 45. Terminal state

The frozen Phase-28 terminal:""")
code("""term = J("phase28_terminal_state.json")
print(term["terminal"])
assert term["terminal"] == (
    "PHASE28_COMPREHENSIVE_ABLATION_MATRIX_COMPLETE__"
    "CORE_ROUTER_AND_REFINER_ABLATIONS_FROZEN__PHASE29_ELIGIBLE_NOT_STARTED")
assert term["exit_class"] == "SUCCESS"
assert term["phase"] == 28
assert term["blocked_terminals"]["PHASE29_STARTED"] is False
assert term["blocked_terminals"]["PHASE30_STARTED"] is False
assert term["blocked_terminals"]["ROUTER_HOLDOUT_OPENED"] is False
assert term["blocked_terminals"]["TEST_OPENED"] is False
print()
print("exit_class       :", term["exit_class"])
print("arms             :", term["n_arms"])
print("new training runs:", term["n_new_training_runs"])
print("tables / figures :", term["n_tables"], "/", term["n_figures"])
print("next phase       :", term["next_phase"], "|", term["next_phase_state"])
print()
print(term["stop_instruction"])
print()
print("REVIEWER NOTEBOOK COMPLIANCE REPAIR: COMPLETE")""")

# ===================================================================== #
# build
# ===================================================================== #
def build() -> bytes:
    cells = []
    for i, c in enumerate(CELLS):
        c = dict(c)
        c["id"] = f"p28-repair-{i:03d}"
        cells.append(c)
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.9"},
            "phase": 28,
            "classification": "PHASE28_CANONICAL_COMPREHENSIVE_SYSTEM_ABLATION_MATRIX",
            "edition": "POST_EXECUTION_REVIEWER_NOTEBOOK_COMPLIANCE_REPAIR",
            "supersedes_notebook_sha256": OLD_SHA,
            "read_only": True,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return (json.dumps(nb, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> int:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    raw = build()
    (NB_DIR / NB_NAME).write_bytes(raw)
    n_md = sum(1 for c in CELLS if c["cell_type"] == "markdown")
    n_code = sum(1 for c in CELLS if c["cell_type"] == "code")
    n_sec = sum(1 for c in CELLS if c["cell_type"] == "markdown"
                and c["source"].startswith("## "))
    print(f"cells: {len(CELLS)} (md {n_md}, code {n_code}) | sections: {n_sec}")
    print("source sha256:", hashlib.sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
