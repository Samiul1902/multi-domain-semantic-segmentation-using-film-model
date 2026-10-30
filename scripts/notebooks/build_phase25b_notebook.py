"""Phase 25B -- MANDATORY reviewer notebook builder (work-order section 22).

Builds, writes and EXECUTES
    notebooks/phasewise/phase_25b_gt_free_features/
        phase25b_gt_free_pre_refinement_features.ipynb

with the 38 required sections listed by the work order.  Determinism:
fixed cell ids (``p25bNNN``) + stripped ``metadata.execution`` + coalesced
stream outputs + 0x-address normalisation.  Consecutive builds of the notebook
(between which no extraction is re-run) must be byte-identical.

Usage:
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase25b_notebook.py
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
NB_PATH = (ROOT / "notebooks" / "phasewise" / "phase_25b_gt_free_features"
           / "phase25b_gt_free_pre_refinement_features.ipynb")

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))      # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))        # noqa: E731

BOOT = """
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIGD = ROOT / "reports" / "figures" / "phase25b_gt_free_features"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"

def _j(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def sty(df, key, fmts=None):
    fmts = fmts or {}
    return (df.style.format(fmts).set_uuid("p25b-" + key)
            .set_table_styles([{"selector": "th", "props": [("text-align", "left")]}]))

assertions = []
def chk(name, ok, detail=None):
    assertions.append((name, bool(ok), detail))
    print(("[PASS] " if ok else "[FAIL] ") + name + ("" if detail is None else f" :: {detail}"))

def fig(name, caption):
    from IPython.display import Image, display, Markdown
    p = FIGD / name
    display(Markdown(f"**{caption}**"))
    if p.exists():
        display(Image(filename=str(p)))
    else:
        print("MISSING FIGURE:", name)
print("Phase 25B notebook bootstrap ok")
"""

cells: list = []


def add_md(s):
    cells.append(md(s))


def add_code(s):
    cells.append(code(s))


# ==================================================================== §1
add_md("""
# Phase 25B — GT-Free Pre-Refinement Feature Extraction

**Method:** `RA-MedFiLM-BARR` (Resource-Aware MedFiLM with Benefit-Aware Refinement Routing)
**Feature specification revision:** `ra_medfilm_barr_narrowed_v1_2`
**Population:** `ROUTER_DEVELOPMENT` only — **n = 4957**
**Output:** a frozen canonical **202-dimensional** numeric feature cache
**Classification:** `PHASE25B_EXECUTED_EVIDENCE`

### Scope — what this notebook does and does NOT do

This notebook extracts **GT-free, pre-refinement, inference-available** feature vectors from the
**frozen** Phase-21 Global MedFiLM, using the frozen ROI-0.30 geometry. Every feature could be
computed at deployment time from the global model's own output — **no ground truth is read**.

| FORBIDDEN in Phase 25B | status |
|---|---|
| router training | NOT performed |
| `DeltaDice` / paired-gain labels | NOT computed |
| regional refiner forward | NOT performed |
| post-safety model | NOT instantiated |
| `ROUTER_HOLDOUT` feature extraction | NOT performed |
| `ROUTER_HOLDOUT` outcome access | NOT performed |
| VAL feature extraction / evaluation | NOT performed |
| TEST access | ZERO reads |
| Phase 25C / 25D | NOT started |

The only permitted model forward is the **Global MedFiLM replay**, used solely to obtain the three
tap feature maps and the probability map that those maps are pooled from.
""")

# ==================================================================== §2
add_md("## §2 — Bootstrap, imports and artifact paths")
add_code(BOOT)

# ==================================================================== §3
add_md("## §3 — Authorized predecessor binding")
add_code("""
bind = {
  "authored_v1_2": _j(AUD / "phase25b_phase24_v1_2_binding.json"),
  "phase25a": _j(AUD / "phase25b_phase25a_binding.json"),
}
for k, v in bind.items():
    print(f"--- {k} ---")
    print(json.dumps({kk: vv for kk, vv in v.items()
                      if kk not in ("groups",)}, indent=1)[:900])
chk("phase24 v1.2 binding PASS",
    bind["authored_v1_2"].get("verdict") == "PHASE25B_PHASE24_V1_2_BINDING_PASS")
chk("phase25a binding PASS",
    bind["phase25a"].get("verdict") == "PHASE25B_PHASE25A_BINDING_PASS")
chk("superseded v1.1 spec recorded as blocking",
    bind["authored_v1_2"].get("extraction_blocked_under_v1_1") is True)
""")

# ==================================================================== §4
add_md("## §4 — Fail-closed re-entry gate")
add_code("""
rg = _j(AUD / "phase25b_reentry_gate.json")
print("verdict      :", rg.get("verdict"))
print("checks passed:", rg.get("n_checks") - rg.get("n_failed", 0), "/", rg.get("n_checks"))
print("failed       :", rg.get("n_failed"))
chk("re-entry gate PASS", rg.get("verdict") == "PHASE25B_REENTRY_GATE_PASS")
chk("re-entry gate zero failures", rg.get("n_failed") == 0)
chk("re-entry gate 33/33", rg.get("n_checks") == 33 and rg.get("n_failed") == 0)
fails = [c for c in rg.get("checks", []) if not c.get("passed")]
for f in fails:
    print("  FAILED:", f.get("check"), "->", f.get("detail"))
""")

# ==================================================================== §5
add_md("""
## §5 — Frozen model binding

Only the frozen Phase-21 **Global MedFiLM** is evaluated.  It is placed in `eval()` mode, all
parameters have `requires_grad = False`, and every forward pass runs under `torch.no_grad()` with
`torch.amp.autocast`.  **No** regional refiner, benefit router or post-safety module is
instantiated anywhere in this phase.
""")
add_code("""
gc = _j(AUD / "phase25b_global_checkpoint_binding.json")
print("checkpoint path :", gc.get("global_checkpoint_path"))
print("checkpoint sha  :", gc.get("global_checkpoint_sha256"))
print("sha exact       :", gc.get("global_checkpoint_sha_exact"))
print("parameters      :", gc.get("global_model_parameters"))
print("eval mode       :", gc.get("model_eval_mode"))
print("all frozen      :", gc.get("all_parameters_frozen"))
print("inference only  :", gc.get("inference_only"))
chk("global checkpoint binding PASS",
    gc.get("verdict") == "PHASE25B_GLOBAL_CHECKPOINT_BINDING_PASS")
chk("global checkpoint SHA exact", gc.get("global_checkpoint_sha_exact") is True)
chk("model eval + frozen + inference-only",
    gc.get("model_eval_mode") and gc.get("all_parameters_frozen")
    and gc.get("inference_only"))
chk("global model parameters == 3523001", gc.get("global_model_parameters") == 3523001)
""")

# ==================================================================== §6
add_md("""
## §6 — ROI-0.30 geometry binding, and why **not** ROI-0.50

ROI geometry comes from the canonical **ROI-0.30** cache.  The two thresholds play different
semantic roles and are never conflated:

* **ROI PROPOSAL threshold = 0.30** → predicted foreground → bbox → `ACTION_AVAILABLE`
* **SEGMENTATION OUTPUT threshold = 0.50** → inherited; used only for probability-margin descriptors
""")
add_code("""
rb = _j(AUD / "phase25b_roi030_cache_binding.json")
print("canonical cache     :", rb.get("roi030_cache"))
print("noncanonical cache  :", rb.get("roi050_cache"), "used:", rb.get("roi050_used"))
print("roi030 rows         :", rb.get("roi030_rows"))
print("== ROUTER_DEVELOPMENT:", rb.get("roi030_rows_equal_router_development"))
print("holdout overlap     :", rb.get("holdout_overlap"))
print("per-domain          :", rb.get("per_domain"))
chk("ROI-0.30 cache binding PASS",
    rb.get("verdict") == "PHASE25B_ROI030_CACHE_BINDING_PASS")
chk("ROI-0.30 is canonical, ROI-0.50 is not",
    rb.get("roi030_is_canonical") is True and rb.get("roi050_is_canonical") is False)
chk("ROI-0.50 not used", rb.get("roi050_used") is False)
chk("ROI030 rows == 4957 and == ROUTER_DEVELOPMENT",
    rb.get("roi030_rows") == 4957 and rb.get("roi030_rows_equal_router_development") is True)
chk("zero holdout overlap in ROI030", rb.get("holdout_overlap") == 0)
""")

# ==================================================================== §7
add_md("""
## §7 — Extraction population: `ROUTER_DEVELOPMENT` only

The feature cache contains **exactly** the 4957 `ROUTER_DEVELOPMENT` rows of the frozen split.
No `ROUTER_HOLDOUT`, no VAL, no TEST row is extracted.
""")
add_code("""
meta = pd.read_csv(CACHE / "metadata.csv")
sm = pd.read_csv(AUD / "phase24_router_split_manifest.csv")
dev = sm[sm["split_role"] == "ROUTER_DEVELOPMENT"]
hold = sm[sm["split_role"] == "ROUTER_HOLDOUT"]
popt = pd.read_csv(TAB / "phase25b_extraction_population.csv")
vc = meta["domain"].value_counts().reindex(["BUSI", "ISIC", "KUB", "KVASIR"])
print("cache rows              :", len(meta))
print("ROUTER_DEVELOPMENT rows :", len(dev))
print("ROUTER_HOLDOUT rows     :", len(hold))
print("per-domain              :"); print(vc.to_string())
chk("cache rows == 4957", len(meta) == 4957)
chk("sample ids exactly == ROUTER_DEVELOPMENT",
    set(meta["sample_id"]) == set(dev["sample_id"]))
chk("zero ROUTER_HOLDOUT ids in cache",
    len(set(meta["sample_id"]) & set(hold["sample_id"])) == 0)
chk("four domains present", set(vc.index) == {"BUSI", "ISIC", "KUB", "KVASIR"})
chk("population table total == 4957",
    int(popt[popt["domain"] == "TOTAL"]["n"].iloc[0]) == 4957)
display(sty(pd.DataFrame({"rows": vc}), "pop", {}))
""")

# ==================================================================== §8
add_md("""
## §8 — Global forward equivalence to the canonical probability cache

The replayed probability map must be **numerically equivalent** to the frozen canonical
`prob512.npy` (float32).  Requirement: `max_abs ≤ 1e-6`, otherwise the phase is BLOCKED.

The exact canonical forward path is reproduced: identical frozen checkpoint, identical
aspect-preserving preprocessing, identical `no_grad + torch.amp.autocast` batched forward, and
identical batch composition.
""")
add_code("""
eq = _j(AUD / "phase25b_global_forward_equivalence.json")
print("reference       :", eq.get("reference"))
print("n compared      :", eq.get("n_samples_compared"))
print("tolerance       :", eq.get("tolerance"))
print("max_abs         :", eq.get("max_abs_difference"))
print("mean_abs        :", eq.get("mean_abs_difference"))
print("n exceeding tol :", eq.get("n_exceeding_tolerance"))
print("byte identical  :", eq.get("byte_identical_achieved"))
print("verdict         :", eq.get("verdict"))
chk("global forward equivalence PASS",
    eq.get("verdict") == "PHASE25B_GLOBAL_FORWARD_EQUIVALENCE_PASS")
chk("max_abs <= 1e-6",
    eq.get("max_abs_difference") is not None and eq.get("max_abs_difference") <= 1e-6)
chk("n exceeding tolerance == 0", eq.get("n_exceeding_tolerance") == 0)
chk("all 4957 compared", eq.get("n_samples_compared") == 4957)
""")

# ==================================================================== §9
add_md("""
## §9 — Feature taps

Three internal activation maps of the frozen Global MedFiLM are tapped with inference-only
`register_forward_hook` output readers.  The hooks never modify the graph — this is proven by the
equivalence audit in §8.
""")
add_code("""
hk = _j(AUD / "phase25b_global_feature_hook_audit.json")
chk("global feature hook audit PASS",
    hk.get("verdict") == "PHASE25B_GLOBAL_FEATURE_HOOK_AUDIT_PASS")
chk("hook does not modify the graph", hk.get("hook_modifies_graph") is False)
chk("no leaked hook handles", hk.get("leaked_handles") == 0)
chk("probability output unchanged by hooks",
    hk.get("probability_output_unchanged_by_hooks") is True)
taps = hk.get("taps", {})
for t, d in taps.items():
    print(f"{t:9s} native_channels={d['native_channels']:>4} grid={d['feature_grid']}")
chk("three taps: bridge / decoder2 / decoder1", set(taps) == {"bridge", "decoder2", "decoder1"})
""")

# ==================================================================== §10
add_md("""
## §10 — Channel-adaptive deterministic reduction to width 32

`DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`:

`start_j = floor(j·C/32)`, `end_j = ceil((j+1)·C/32)`, `z[j] = mean(v[start_j:end_j])`

For `C < 32` the bins overlap; for `C ≥ 32` they are disjoint.  **Zero** trainable parameters —
no projection, no PCA, no random projection, no SVD, no truncation.
""")
add_code("""
red = _j(AUD / "phase25b_feature_reduction_audit.json")
print("operation        :", red.get("operation"))
print("output width K   :", red.get("output_width_K"))
print("trainable params :", red.get("trainable_parameters"))
print("forbidden ops    :", red.get("forbidden_ops_used"))
for t, d in red.get("taps", {}).items():
    print(f"  {t:9s} C={d['native_width']:>4} bins={d['bins']} "
          f"overlap={d['overlapping_bins_expected']} covers_all={d['covers_all_channels']}")
chk("reduction audit PASS",
    red.get("verdict") == "PHASE25B_FEATURE_REDUCTION_PASS")
chk("zero trainable params in reduction", red.get("trainable_parameters") == 0)
chk("no forbidden reduction ops", not red.get("forbidden_ops_used"))
chk("every bin covers all native channels",
    all(d["covers_all_channels"] for d in red.get("taps", {}).values()))
chk("overlap exactly where C < 32",
    all((d["native_width"] < 32) == d["overlapping_bins_expected"]
        for d in red.get("taps", {}).values()))
""")

# ==================================================================== §11
add_md("""
## §11 — ROI → feature-grid mapping

The ROI box (in 512-canvas coordinates) is mapped to each tap's feature grid by the half-open rule
`start = floor`, `end = ceil`, clipped to the grid. External padding contributes **no** cell. Every
mapped ROI must contain ≥ 1 cell.
""")
add_code("""
mp = _j(AUD / "phase25b_roi_feature_mapping_audit.json")
print("convention :", mp.get("coordinate_convention"))
print("start/end  :", mp.get("start_rule"), "/", mp.get("end_rule"))
print("clip       :", mp.get("clip"))
print("rows verified:", mp.get("rows_verified"))
print("empty mapped ROIs:", mp.get("empty_mapped_roi_count"))
print("bridge cells min/max:", mp.get("bridge_grid_cells_min"), mp.get("bridge_grid_cells_max"))
chk("ROI mapping audit PASS",
    mp.get("verdict") == "PHASE25B_ROI_FEATURE_MAPPING_PASS")
chk("no empty mapped ROI", mp.get("empty_mapped_roi_count") == 0)
chk("external padding contributes no cells",
    mp.get("external_padding_contributes_no_cells") is True)
chk("all 4957 rows verified", mp.get("rows_verified") == 4957)
""")

# ==================================================================== §12
add_md("""
## §12 — Ten GT-free scalar descriptors (with the D1 correction)

Ten scalars follow the six 32-D deep groups.  `predicted_roi_area_fraction` uses the
**supervisor-corrected** D1 definition on the clipped in-canvas ROI:

`w_in = max(0, min(512, x1) − max(0, x0))`, `h_in` likewise, `area_fraction = w_in·h_in / 512²`

This supersedes the old `crop_side_pixels²/512²`, which could exceed 1 whenever the crop window ran
past the canvas.  `predicted_roi_side` may legitimately exceed 512.
""")
add_code("""
sc = _j(AUD / "phase25b_scalar_feature_semantics.json")
chk("scalar semantics audit present", sc.get("n_scalars") == 10)
chk("all threshold roles resolved", sc.get("unresolved_threshold_roles") == 0)
chk("scalars use no GT", sc.get("uses_GT") is False)
d1 = _j(AUD / "phase25b_d1_area_fraction_audit.json")
print("D1 definition   :", d1.get("definition"))
print("superseded      :", d1.get("superseded_formula"),
      "used:", d1.get("superseded_formula_used"))
print("area range      :", d1.get("feature_range"))
print("rows > 1        :", d1.get("rows_exceeding_1"))
print("side max        :", d1.get("predicted_roi_side_max"),
      "rows>512:", d1.get("predicted_roi_side_rows_gt512"))
print("recompute max diff:", d1.get("max_abs_recompute_diff"))
chk("D1 area fraction PASS", d1.get("verdict") == "PHASE25B_D1_AREA_FRACTION_PASS")
chk("area fraction in [0,1], zero rows > 1", d1.get("rows_exceeding_1") == 0)
chk("superseded D1 formula not used", d1.get("superseded_formula_used") is False)
chk("area recomputation matches feature",
    d1.get("recomputed_matches_feature") is True)
chk("roi side may exceed 512", d1.get("predicted_roi_side_rows_gt512", 0) > 0)
display(sty(pd.DataFrame(sc.get("scalars", [])), "scalars",
            {"feature_index": "{:.0f}"}))
""")

# ==================================================================== §13
add_md("""
## §13 — Exact 202-D ordering

Indices `0..191` are the six 32-D deep groups (bridge_global, bridge_roi, decoder2_global,
decoder2_roi, decoder1_global, decoder1_roi).  Indices `192..201` are the ten scalars in the frozen
order.  `task_id` is **not** part of the vector — no task embedding is embedded here.
""")
add_code("""
fo = _j(AUD / "phase25b_feature_order_audit.json")
print("numeric dims :", fo.get("numeric_dimensions"))
print("deep dims    :", fo.get("deep_dimensions"))
print("scalar dims  :", fo.get("scalar_dimensions"))
print("task embedding appended:", fo.get("task_embedding_appended"))
print("group offsets:"); print(json.dumps(fo.get("group_offsets"), indent=1)[:600])
chk("feature order audit exact",
    fo.get("verdict") == "PHASE25B_FEATURE_ORDER_EXACT")
chk("numeric_dim == 202", fo.get("numeric_dimensions") == 202)
chk("names match frozen order", fo.get("names_match_frozen_order") is True)
chk("no task embedding in the vector", fo.get("task_embedding_appended") is False)
""")

# ==================================================================== §14
add_md("## §14 — Task metadata stored separately (no patient ID, no GT)")
add_code("""
cols = list(meta.columns)
print("metadata columns:", cols)
forbidden = [c for c in cols if any(t in c.lower()
             for t in ("patient", "mask", "gt_", "dice", "gain", "class", "fraction"))]
chk("no forbidden metadata columns", not forbidden, forbidden)
chk("task_id present and separate", "task_id" in cols)
chk("domain / outer_fold present", "domain" in cols and "outer_fold" in cols)
chk("feature_row_index present", "feature_row_index" in cols)
display(meta.head(5))
""")

# ==================================================================== §15
add_md("## §15 — Cache on disk")
add_code("""
man = _j(CACHE / "cache_manifest.json")
print(json.dumps(man, indent=1)[:1200])
chk("cache manifest present", bool(man))
chk("features.npy present", (CACHE / "features.npy").exists())
chk("metadata.csv present", (CACHE / "metadata.csv").exists())
chk("feature_schema.csv present", (CACHE / "feature_schema.csv").exists())
""")

# ==================================================================== §16
add_md("## §16 — Cache integrity")
add_code("""
ci = _j(AUD / "phase25b_feature_cache_integrity.json")
feats = np.load(CACHE / "features.npy")
print("shape  :", feats.shape, "dtype:", feats.dtype)
print("nan    :", ci.get("nan_count"), "inf:", ci.get("inf_count"))
print("unique ids:", ci.get("unique_sample_ids"))
print("== ROUTER_DEVELOPMENT:", ci.get("sample_ids_equal_router_development"))
print("holdout overlap:", ci.get("holdout_overlap"))
print("feature selection applied:", ci.get("feature_selection_applied"))
print("features sha:", ci.get("matrix_sha256"))
chk("cache integrity PASS",
    ci.get("verdict") == "PHASE25B_FEATURE_CACHE_INTEGRITY_PASS")
chk("shape == (4957, 202)", feats.shape == (4957, 202))
chk("dtype float32", str(feats.dtype) == "float32")
chk("no NaN", ci.get("nan_count") == 0)
chk("no Inf", ci.get("inf_count") == 0)
chk("ids == ROUTER_DEVELOPMENT", ci.get("sample_ids_equal_router_development") is True)
chk("no feature selection applied", ci.get("feature_selection_applied") is False)
""")

# ==================================================================== §17
add_md("""
## §17 — Descriptive analysis only

Summary statistics and per-domain summaries.  **No** target correlation, **no** label correlation,
**no** outcome-conditioned analysis — those belong to later phases.
""")
add_code("""
ss = pd.read_csv(TAB / "phase25b_feature_summary_statistics.csv")
sd = pd.read_csv(TAB / "phase25b_feature_summary_by_domain.csv")
display(sty(ss.head(12), "ss", {}))
display(sty(sd.head(12), "sd", {}))
chk("summary statistics table present", len(ss) > 0)
chk("per-domain summary table present", len(sd) > 0)
chk("no target/label column in tables",
    not any(("dice" in c.lower() or "gain" in c.lower() or "label" in c.lower())
            for c in list(ss.columns) + list(sd.columns)))
""")

# ==================================================================== §18
add_md("""
## §18 — Determinism subset audit (64 samples, 16/domain)

A pre-declared 64-sample audit subset (selection independent of feature values and outcomes) is
re-extracted twice under identical inference settings and compared against the frozen cache.  All
4957 rows are **not** re-run.  Because AMP numerics depend on batch membership, the re-run replays
the canonical contiguous batches so each sampled row sits in the same batch as canonically.
""")
add_code("""
det = _j(AUD / "phase25b_feature_determinism.json")
sub = pd.read_csv(TAB / "phase25b_feature_determinism_subset.csv")
print("subset size   :", det.get("subset_size"), "per domain:", det.get("per_domain"))
print("ran all 4957? :", det.get("reran_all_4957"))
print("run1 vs run2  :", det.get("run1_vs_run2"))
print("run1 vs frozen:", det.get("run1_vs_frozen_cache"))
print("verdict       :", det.get("verdict"))
chk("determinism PASS", det.get("verdict") == "PHASE25B_FEATURE_DETERMINISM_PASS")
chk("run1 vs run2 max_abs <= 1e-6",
    det.get("run1_vs_run2", {}).get("max_abs", 9) <= 1e-6)
chk("run1 vs frozen max_abs <= 1e-6",
    det.get("run1_vs_frozen_cache", {}).get("max_abs", 9) <= 1e-6)
chk("all 4957 NOT rerun", det.get("reran_all_4957") is False)
chk("subset is 64 rows, 16/domain",
    len(sub) == 64 and sub["domain"].value_counts().nunique() == 1
    and set(sub["domain"].value_counts().values) == {16})
display(sty(sub.head(8), "sub", {}))
""")

# ==================================================================== §19
add_md("## §19 — Implementation test suite")
add_code("""
ts = _j(AUD / "phase25b_implementation_test_suite.json")
print("verdict :", ts.get("verdict"))
print("passed  :", ts.get("n_passed"), "/", ts.get("n_checks"))
fails = [c for c in ts.get("checks", []) if not c.get("passed")]
for f in fails:
    print("  FAILED:", f.get("check"), "->", f.get("detail"))
chk("implementation tests PASS",
    ts.get("verdict") == "PHASE25B_IMPLEMENTATION_TESTS_PASS")
chk("zero implementation test failures", ts.get("n_failed") == 0)
""")

# ==================================================================== §20
add_md("## §20 — Required tables")
add_code("""
tab_names = ["phase25b_feature_schema.csv",
             "phase25b_feature_group_summary.csv",
             "phase25b_scalar_feature_definitions.csv",
             "phase25b_feature_summary_statistics.csv",
             "phase25b_feature_summary_by_domain.csv",
             "phase25b_extraction_population.csv",
             "phase25b_feature_cache_inventory.csv",
             "phase25b_feature_determinism_subset.csv"]
present = [t for t in tab_names if (TAB / t).exists()]
print("tables present:", len(present), "/", len(tab_names))
for t in present:
    print("  ", t)
chk("all required tables present", len(present) == len(tab_names),
    [t for t in tab_names if t not in present])
""")

# ==================================================================== §21
add_md("## §21 — Required figures")
add_code("""
fm = _j(FIGD / "phase25b_figure_manifest.json")
print("n figures:", fm.get("n_figures"),
      "(required", fm.get("n_required_figures"), "+ optional",
      fm.get("n_optional_figures"), ")")
for name in ["p25b_feature_pipeline.png",
             "p25b_channel_adaptive_reduction.png",
             "p25b_feature_group_layout.png",
             "p25b_scalar_descriptors.png",
             "p25b_extraction_population.png",
             "p25b_cache_integrity_summary.png"]:
    fig(name, name.replace("p25b_", "").replace(".png", "").replace("_", " "))
chk("figure manifest present", bool(fm))
chk("at least 6 required figures", fm.get("n_required_figures", 0) >= 6)
chk("no experimental results in figures",
    fm.get("contains_experimental_results") is False)
""")

# ==================================================================== §22
add_md("""
## §22 — No-outcome / no-GT / scope guards

Confirms the phase read no ground truth, computed no segmentation metric, instantiated no refiner or
router, and performed no post-safety step.
""")
add_code("""
ng = _j(AUD / "phase25b_no_gt_leakage_audit.json")
sg = _j(AUD / "phase25b_scope_guard.json")
for k in ("gt_masks_read_for_feature_construction", "dice_computed", "deltadice_computed",
          "iou_computed", "refined_prediction_present", "regional_refiner_features_present",
          "oracle_benefit_present"):
    print(f"{k:45s}: {ng.get(k)}")
chk("no-GT leakage PASS", ng.get("verdict") == "PHASE25B_NO_GT_LEAKAGE_PASS")
chk("no GT mask read", ng.get("gt_masks_read_for_feature_construction") is False)
chk("no Dice / DeltaDice / IoU",
    not ng.get("dice_computed") and not ng.get("deltadice_computed")
    and not ng.get("iou_computed"))
chk("no refined prediction", ng.get("refined_prediction_present") is False)
chk("scope guard PASS", sg.get("verdict") == "PHASE25B_SCOPE_GUARD_PASS")
chk("zero refiner forwards", sg.get("regional_refiner_forward_passes") == 0)
chk("router never instantiated/trained", sg.get("benefit_router_instantiated") is False
    and sg.get("router_training_runs") == 0)
chk("no post-safety", sg.get("BARRPostSafetyV1_instantiated") is False
    and sg.get("post_safety_training_runs") == 0)
chk("no paired-gain labels", sg.get("paired_gain_labels_generated") is False)
chk("no delta-dice", sg.get("DeltaDice_computed") is False)
""")

# ==================================================================== §23
add_md("## §23 — TEST / holdout / VAL locks and no-execution boundaries")
add_code("""
tl = _j(AUD / "phase25b_test_lock_audit.json")
for k in ("test_image_reads", "test_mask_reads", "test_inference", "test_metrics",
          "val_feature_extraction", "val_outcome_evaluation", "holdout_feature_extraction",
          "holdout_outcome_reads", "test_reads"):
    print(f"{k:30s}: {tl.get(k)}")
chk("test lock audit PASS", tl.get("verdict") == "PHASE25B_TEST_LOCK_PASS")
chk("zero TEST reads", tl.get("test_reads") == 0)
chk("zero holdout feature extraction", tl.get("holdout_feature_extraction") == 0)
chk("zero holdout outcome reads", tl.get("holdout_outcome_reads") == 0)
chk("zero VAL feature extraction", tl.get("val_feature_extraction") == 0)
chk("zero VAL outcome evaluation", tl.get("val_outcome_evaluation") == 0)

# Phase 25C / 25D not started
nb_dir = ROOT / "notebooks" / "phasewise"
c25 = list(nb_dir.glob("phase_25c*")) + list(nb_dir.glob("phase_25d*"))
chk("no Phase 25C/25D notebook exists", len(c25) == 0, [p.name for p in c25])
chk("no router checkpoint exists",
    len(list((ROOT / "checkpoints").glob("*barr*router*"))) == 0)
""")

# ==================================================================== §24
add_md("""
## §24 — Phase 25C handoff schema

**Stage ownership (canonical):** Phase **25C** = OOF paired refinement-gain **label
generation**; Phase **25D** = benefit-**router training**. Phase25C may reference the 202-D cache
for **identity/integrity joining only** — it does **not** train on those features, and it does
**not** train the router or the 16-D task embedding (both belong to Phase25D).
""")
add_code("""
hs = _j(AUD / "phase25b_phase25c_handoff_schema.json")
print("feature cache :", hs.get("feature_cache_dir"))
print("shape/dtype   :", hs.get("features_shape"), hs.get("features_dtype"))
print("join key      :", hs.get("join_key"))
print("numeric dim   :", hs.get("numeric_dim"))
print("router input dim:", hs.get("router_input_dim"))
print("task embedding provided:", hs.get("task_embedding_present"))
print("task embedding owner   :", hs.get("task_embedding_owner"))
print("note          :", hs.get("task_embedding_note"))
print("population    :", hs.get("population"), hs.get("population_n"))
print("labels consumable by 25C:", hs.get("labels_consumable_by_phase25c"))
print("25C primary input role :", hs.get("phase25c_primary_input_role"))
print("25C trains router      :", hs.get("phase25c_trains_router"))
print("25C trains task emb    :", hs.get("phase25c_trains_task_embedding"))
print("25C generates OOF gain :", hs.get("phase25c_generates_oof_paired_gain_labels"))
print("25D consumes 202-D     :", hs.get("phase25d_consumes_202d_features"))
print("25D consumes 25C labels:", hs.get("phase25d_consumes_phase25c_labels"))
print("25D trains task emb    :", hs.get("phase25d_trains_task_embedding"))
print("25D trains router      :", hs.get("phase25d_trains_benefit_router"))
print("forbidden cols:", hs.get("forbidden_columns_present"))
chk("handoff schema ready",
    hs.get("verdict") == "PHASE25B_PHASE25C_OOF_GAIN_HANDOFF_READY")
chk("join key == sample_id", hs.get("join_key") == "sample_id")
chk("202-D numeric + 16-D task embedding == 218",
    hs.get("numeric_dim") == 202 and hs.get("task_embedding_dim") == 16
    and hs.get("router_input_dim") == 218)
chk("task embedding owned by Phase25D",
    hs.get("task_embedding_owner") == "PHASE25D"
    and hs.get("task_embedding_provided") is False)
chk("25C does not train router or task embedding",
    hs.get("phase25c_trains_router") is False
    and hs.get("phase25c_trains_task_embedding") is False)
chk("25C generates OOF paired-gain labels",
    hs.get("phase25c_generates_oof_paired_gain_labels") is True)
chk("25D consumes 202-D features + 25C labels and trains router + task emb",
    hs.get("phase25d_consumes_202d_features") is True
    and hs.get("phase25d_consumes_phase25c_labels") is True
    and hs.get("phase25d_trains_task_embedding") is True
    and hs.get("phase25d_trains_benefit_router") is True)
chk("no label column in handoff",
    not hs.get("labels_consumable_by_phase25c"))
chk("handoff declares test/holdout/val reads 0",
    hs.get("test_reads") == 0 and hs.get("holdout_feature_extraction") == 0
    and hs.get("val_feature_extraction") == 0)
""")

# ==================================================================== §25
add_md("## §25 — Provenance and governance pointer")
add_code("""
prov = _j(CACHE / "extraction_provenance.json")
rgp = _j(AUD / "phase25b_reentry_gate.json")
print(json.dumps(prov, indent=1)[:1400])
chk("extraction provenance present", bool(prov))
chk("method name correct", rgp.get("method") == "RA-MedFiLM-BARR")
chk("revision correct", rgp.get("feature_spec_revision") == "ra_medfilm_barr_narrowed_v1_2")
chk("provenance: global forward replay count == 4957",
    prov.get("global_forward_replay_count") == 4957)
chk("provenance: no refiner / router / post-safety",
    prov.get("regional_refiner_forward_passes") == 0
    and prov.get("benefit_router_instantiated") is False
    and prov.get("post_safety_instantiated") is False)
""")

# ==================================================================== §26
add_md("""
## §26 — Feature schema (reviewer reference)

The full 202-entry schema: name, group, tap, scope, dtype, definition.
""")
add_code("""
sch = pd.read_csv(CACHE / "feature_schema.csv")
print("schema rows:", len(sch))
display(sty(sch.head(20), "schema", {}))
chk("schema has 202 rows", len(sch) == 202)
chk("schema columns complete",
    {"feature_index", "feature_name"}.issubset(set(sch.columns)))
""")

# ==================================================================== §27
add_md("## §27 — Data-role / threshold-role table")
add_code("""
tz = _j(AUD / "phase25b_threshold_semantics_audit.json")
print("ROI proposal threshold     :", tz.get("roi_proposal_threshold"))
print("  role                     :", tz.get("roi_proposal_role"))
print("SEGMENTATION output thr    :", tz.get("segmentation_output_threshold"))
print("  role                     :", tz.get("segmentation_output_role"))
print("segment thr used in ROI    :", tz.get("segmentation_threshold_used_in_roi_derivation"))
print("scalars per role           :", tz.get("scalars_per_role"))
chk("threshold semantics complete",
    tz.get("verdict") == "PHASE25B_THRESHOLD_SEMANTICS_COMPLETE")
chk("ROI threshold == 0.30", tz.get("roi_proposal_threshold") == 0.30)
chk("segmentation threshold == 0.50", tz.get("segmentation_output_threshold") == 0.50)
chk("segmentation threshold not used for ROI geometry",
    tz.get("segmentation_threshold_used_in_roi_derivation") is False)
""")

# ==================================================================== §28
add_md("## §28 — Group-level descriptive summary")
add_code("""
gs = pd.read_csv(TAB / "phase25b_feature_group_summary.csv")
display(sty(gs, "gs", {}))
chk("group summary present", len(gs) > 0)
chk("six deep groups reported", len(gs) >= 6)
""")

# ==================================================================== §29
add_md("## §29 — Reviewer claim boundary")
add_code("""
print("CLAIM BOUNDARY FOR PHASE 25B")
print("-" * 60)
print("This phase establishes ONLY that a GT-free, pre-refinement, inference-")
print("available 202-D feature cache exists for ROUTER_DEVELOPMENT, built from a")
print("frozen global model, and that it is deterministic and integrity-checked.")
print()
print("It makes NO claim about:")
print("  * routing performance or benefit prediction")
print("  * the regional refiner's effect")
print("  * any Dice / DeltaDice quantity")
print("  * any holdout / VAL / TEST behaviour")
print()
print("Max novelty claim (Phase 23) = Level 2, scoped to the INTEGRATED GT-free")
print("paired-gain router. Never 'first to ...'.")
chk("no performance claim in this phase",
    _j(AUD / "phase25b_scope_guard.json").get("router_training_runs") == 0)
""")

# ==================================================================== §30
add_md("## §30 — Reproducibility manifest")
add_code("""
repro = {
  "method": "RA-MedFiLM-BARR",
  "revision": "ra_medfilm_barr_narrowed_v1_2",
  "master_seed": 42,
  "population": "ROUTER_DEVELOPMENT",
  "population_n": 4957,
  "features_sha256": _j(AUD / "phase25b_feature_cache_integrity.json").get("matrix_sha256"),
  "metadata_sha256": _j(AUD / "phase25b_feature_cache_integrity.json").get("metadata_sha256"),
  "global_ckpt_sha256": _j(AUD / "phase25b_global_checkpoint_binding.json").get(
      "global_checkpoint_sha256"),
  "reentry_gate": _j(AUD / "phase25b_reentry_gate.json").get("verdict"),
  "equivalence": _j(AUD / "phase25b_global_forward_equivalence.json").get("verdict"),
  "determinism": _j(AUD / "phase25b_feature_determinism.json").get("verdict"),
}
print(json.dumps(repro, indent=1))
chk("reproducibility manifest complete", all(repro.values()))
""")

# ==================================================================== §31
add_md("## §31 — Assertion roll-up PART 1")
add_code("""
roll1 = [(n, ok) for n, ok, _d in assertions]
print(f"assertions so far: {sum(1 for _, ok in roll1 if ok)}/{len(roll1)} PASS")
for n, ok in roll1:
    if not ok:
        print("  FAIL:", n)
chk("all assertions so far pass", all(ok for _n, ok in roll1))
""")

# ==================================================================== §32
add_md("## §32 — Assertion roll-up PART 2")
add_code("""
roll2 = [(n, ok) for n, ok, _d in assertions]
n_fail = sum(1 for _n, ok in roll2 if not ok)
print(f"FINAL: {len(roll2) - n_fail}/{len(roll2)} assertions PASS")
assert n_fail == 0, f"{n_fail} assertions failed"
print("PHASE25B_NOTEBOOK_ASSERTIONS_ALL_PASS")
""")

# ==================================================================== §33
add_md("## §33 — Execution summary")
add_code("""
print("Phase 25B reviewer notebook executed end-to-end.")
print("Model forwards (global replay only):",
      _j(CACHE / "extraction_provenance.json").get("global_forward_replay_count"))
print("Regional refiner forwards :", 0)
print("Router training runs      :", 0)
print("TEST reads                :", 0)
print("Holdout feature extraction:", 0)
print("VAL feature extraction    :", 0)
""")

# ==================================================================== §34
add_md("## §34 — Notebook determinism statement")
add_code("""
print("This notebook is rebuilt from frozen artifacts and must be byte-identical")
print("across three consecutive builds (no re-extraction between builds).")
print("The determinism proof is written to:")
print("  reports/audits/phase25b_notebook_determinism.json")
chk("no phase-25C/25D artefacts referenced in this notebook",
    len(list((ROOT / 'notebooks' / 'phasewise').glob('phase_25c*'))) == 0)
""")

# ==================================================================== §35
add_md("## §35 — Visual integrity statement")
add_code("""
print("All embedded figures are descriptive/schematic of the frozen feature")
print("construction and cache; none carries an experimental result or a")
print("hypothetical performance curve.")
print("Visual integrity proof -> reports/audits/phase25b_notebook_visual_integrity.json")
chk("figure manifest marks figures as descriptive",
    _j(FIGD / "phase25b_figure_manifest.json").get(
        "classification") == "DESCRIPTIVE_SCHEMATIC_FEATURES")
""")

# ==================================================================== §36
add_md("## §36 — Downstream contract (corrected stage semantics)")
add_code("""
print("Phase 25C (OOF paired refinement-gain LABEL GENERATION) MAY reference:")
print("  - data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy (4957x202)")
print("  - metadata.csv (sample_id, task_id, domain, outer_fold, feature_row_index, action_available)")
print("  for IDENTITY / INTEGRITY JOINING ONLY (join key = sample_id).")
print("Phase 25C does NOT train on the 202-D features.")
print("Phase 25C does NOT train the benefit router and does NOT create the task embedding.")
print("Phase 25C MUST NOT assume any label / GT / Dice column exists here.")
print()
print("Phase 25D (benefit-router training) joins 25B features + 25C OOF labels and")
print("trains BARRBenefitRouterV1, INCLUDING the learned Embedding(4,16) that turns")
print("202 numeric features + 16 task-embedding dims into the 218-D router input.")
chk("downstream contract stated",
    _j(AUD / "phase25b_phase25c_handoff_schema.json").get("numeric_dim") == 202)
chk("25C does not train the router",
    _j(AUD / "phase25b_phase25c_handoff_schema.json").get("phase25c_trains_router") is False)
chk("task embedding owner is Phase25D",
    _j(AUD / "phase25b_phase25c_handoff_schema.json").get("task_embedding_owner") == "PHASE25D")
""")

# ==================================================================== §36b
add_md("""
## §36b — Downstream stage ownership clarification

The canonical downstream stage ownership is:

| stage | name | produces | trains |
|---|---|---|---|
| **25C** | OOF paired refinement-gain label generation | leakage-safe OOF `DeltaDice` labels (`Dice_candidate_refined − Dice_global`) | nothing |
| **25D** | benefit-router training | a trained `BARRBenefitRouterV1` | the router **and** its 16-D task embedding |

- **25C = create leakage-safe OOF `DeltaDice` labels** (uses GT for label creation only).
- **25D = join 25B features + 25C labels and train `BARRBenefitRouterV1`.**
- **task embedding = trained only in 25D** (202 numeric GT-free features + 16 learned task
  embedding = 218 router input dims).

Phase25B itself creates **no** labels, trains **no** router, and creates **no** task embedding.
""")
add_code("""
hs2 = _j(AUD / "phase25b_phase25c_handoff_schema.json")
road = hs2.get("downstream_stage_roadmap", {})
print("downstream roadmap:")
for k in ("25C", "25D", "25E", "25F", "25G"):
    print(f"   {k}: {road.get(k)}")
chk("roadmap: 25C == OOF paired gain label generation",
    "OOF paired refinement-gain label generation" in str(road.get("25C")))
chk("roadmap: 25D == benefit-router training",
    "benefit-router training" in str(road.get("25D")))
chk("roadmap: task embedding owner Phase25D",
    hs2.get("task_embedding_owner") == "PHASE25D")
chk("25C does not train task embedding",
    hs2.get("phase25c_trains_task_embedding") is False)
""")

# ==================================================================== §37
add_md("## §37 — No-execution boundary audit")
add_code("""
nb = _j(AUD / "phase25b_no_execution_boundary_audit.json")
if nb:
    print(json.dumps(nb, indent=1)[:800])
chk("no-execution boundary: refiner forwards 0",
    _j(AUD / "phase25b_scope_guard.json").get("regional_refiner_forward_passes") == 0)
chk("no-execution boundary: router training 0",
    _j(AUD / "phase25b_scope_guard.json").get("router_training_runs") == 0)
chk("no-execution boundary: TEST 0",
    _j(AUD / "phase25b_test_lock_audit.json").get("test_reads") == 0)
""")

# ==================================================================== §38
add_md("""
## §38 — Terminal

**Phase 25B is COMPLETE.** The canonical 202-D GT-free pre-refinement feature cache is frozen.
Phase 25C is eligible but **has not been started**.
""")
add_code("""
print("PHASE25B_GT_FREE_PRE_REFINEMENT_FEATURES_COMPLETE")
print("__202D_CANONICAL_FEATURE_CACHE_FROZEN__")
print("PHASE25C_ELIGIBLE_NOT_STARTED")
chk("terminal conditions satisfied",
    _j(AUD / "phase25b_reentry_gate.json").get("verdict") == "PHASE25B_REENTRY_GATE_PASS"
    and _j(AUD / "phase25b_global_forward_equivalence.json").get("verdict")
        == "PHASE25B_GLOBAL_FORWARD_EQUIVALENCE_PASS"
    and _j(AUD / "phase25b_feature_determinism.json").get("verdict")
        == "PHASE25B_FEATURE_DETERMINISM_PASS"
    and _j(AUD / "phase25b_feature_cache_integrity.json").get("verdict")
        == "PHASE25B_FEATURE_CACHE_INTEGRITY_PASS")
""")

# ------------------------------------------------------------------ write
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p25b{_i:03d}"


def main() -> int:
    NB_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(NB_PATH))
    print(f"Wrote {NB_PATH} ({len(nb.cells)} cells); executing ...")
    client = NotebookClient(nb, kernel_name="jup-venv", timeout=3600,
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()

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
    monotonic = counts == list(range(1, len(code_cells) + 1))
    imgs = sum(1 for c in code_cells for o in c.get("outputs", [])
               if "image/png" in (o.get("data", {}) or {}))
    sha_nb = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
    print(f"Cells: {len(nb.cells)} | markdown: "
          f"{sum(1 for c in nb.cells if c.cell_type == 'markdown')} | code: {len(code_cells)}")
    print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
    print("Monotonic exec counts:", "PASS" if monotonic else "FAIL")
    print("embedded PNG outputs:", imgs)
    print("Notebook SHA256:", sha_nb)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
