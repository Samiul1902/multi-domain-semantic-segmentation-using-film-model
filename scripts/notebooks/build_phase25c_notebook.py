"""Phase 25C -- MANDATORY reviewer notebook builder (work-order section 24).

Builds, writes and EXECUTES
    notebooks/phasewise/phase_25c_paired_gain_labels/
        phase25c_oof_paired_refinement_gain.ipynb

41 sections. Determinism: fixed cell ids (``p25cNNN``) + stripped
``metadata.execution`` + coalesced stream outputs + 0x-address normalisation.
The notebook ONLY reads the frozen Phase25C artifacts + the frozen label table
(no refiner inference is re-run).

Usage:
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase25c_notebook.py
"""
from __future__ import annotations

import base64
import hashlib
import re
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
NB_PATH = (ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels"
           / "phase25c_oof_paired_refinement_gain.ipynb")

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))      # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))        # noqa: E731

BOOT = """
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "notebooks/phasewise/phase_25c_paired_gain_labels/code"))
import phase25c_common as C
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIGD = ROOT / "reports" / "figures" / "phase25c_paired_gain_labels"

def _j(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def sty(df, key, fmts=None):
    fmts = fmts or {}
    return (df.style.format(fmts).set_uuid("p25c-" + key)
            .set_table_styles([{"selector": "th", "props": [("text-align", "left")]}]))

assertions = []
def chk(name, ok, detail=None):
    assertions.append((name, bool(ok), detail))
    print(("[PASS] " if ok else "[FAIL] ") + name + ("" if detail is None else f" :: {detail}"))

def fig(name, caption):
    # Embed a frozen on-disk PNG verbatim. The bytes on disk are the artifact of
    # record, so they are passed explicitly -- Image(filename=...) re-reads (and, for
    # an in-flight mpl writer, can observe a torn/truncated tail), whereas
    # Image(data=...) fixes the payload at call time.
    from IPython.display import Image, display, Markdown
    p = FIGD / name
    display(Markdown(f"**{caption}**"))
    if not p.exists():
        print("MISSING FIGURE:", name)
        return
    raw = p.read_bytes()
    assert raw[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10]), f"unusable figure: {name}"
    assert raw.rfind(b"IEND") >= len(raw) - 12, f"unusable figure (no IEND): {name}"
    display(Image(data=raw))

LAB = pd.read_csv(C.LABEL_CSV)
print("Phase 25C notebook bootstrap ok; label rows:", len(LAB))
"""

cells: list = []


def add_md(s):
    cells.append(md(s))


def add_code(s):
    cells.append(code(s))


# ==================================================================== §1
add_md("""
# Phase 25C — Leakage-Safe OOF Paired Refinement-Gain Label Generation

**Method:** `RA-MedFiLM-BARR` — Resource-Aware MedFiLM with Benefit-Aware Refinement Routing
**Feature specification revision:** `ra_medfilm_barr_narrowed_v1_2`
**Population:** `ROUTER_DEVELOPMENT` only — **n = 4957**
**Output:** a frozen canonical **OOF paired-gain label table**
**Classification:** `PHASE25C_EXECUTED_EVIDENCE`

### Scientific scope

For every action-available `ROUTER_DEVELOPMENT` sample *i*:

```
DeltaDice_i = Dice(candidate_refined_i, y_i) - Dice(global_i, y_i)
```

using **OUT-OF-FOLD** regional-refiner predictions only: sample *i* is scored by the fold-specific
canonical ROI-0.30 refiner whose **outer target fold** contains *i* — a fold that was completely
excluded from that refiner's gradient fitting, early-stop fitting and checkpoint selection.

`DeltaDice` is the **paired refinement gain**. It is **NOT** a causal / counterfactual effect, and it
is **NOT** a deployable router input feature.

### What Phase 25C does NOT do

| FORBIDDEN in Phase 25C | status |
|---|---|
| benefit-router training | NOT performed — Phase 25D |
| 16-D task-embedding training | NOT performed — Phase 25D |
| use of the Phase25A **final** refiner for OOF labels | NOT performed |
| `ROUTER_HOLDOUT` use | ZERO |
| VAL808 use | ZERO |
| TEST access | ZERO reads |
| Global MedFiLM re-run | ZERO forwards (p_global from the frozen cache) |
| Phase 25D start | NOT started |
""")

# ==================================================================== §2
add_md("## §2 — Bootstrap, imports and artifact paths")
add_code(BOOT)

# ==================================================================== §3
add_md("## §3 — Authorized predecessor binding")
add_code("""
repair = _j(AUD / "phase25b_stage_semantics_repair_final_check.json")
print("predecessor terminal:", repair.get("terminal"))
chk("predecessor terminal exact",
    repair.get("terminal") == C.EXPECTED["predecessor_terminal"],
    repair.get("terminal"))
chk("predecessor repair all_pass", repair.get("all_pass") is True)
""")

# ==================================================================== §4
add_md("## §4 — Phase24 v1.2 binding")
add_code("""
b24 = _j(AUD / "phase25c_phase24_binding.json")
print(json.dumps({k: b24[k] for k in ("phase24_v1_2_status",
      "phase24_notebook_sha_matches", "roi_proposal_threshold",
      "segmentation_output_threshold")}, indent=1))
chk("phase24 v1.2 COMPLETE_FROZEN", b24.get("phase24_v1_2_status") == "COMPLETE_FROZEN")
chk("phase24 notebook SHA exact", b24.get("phase24_notebook_sha_matches") is True)
""")

# ==================================================================== §5
add_md("## §5 — Phase25A binding")
add_code("""
b25a = _j(AUD / "phase25c_phase25a_binding.json")
print(json.dumps({k: b25a[k] for k in ("phase25a_notebook_sha_matches",
      "crossfit_protocol_verdict", "outer_folds",
      "final_refiner_used_for_oof")}, indent=1))
chk("phase25a notebook SHA exact", b25a.get("phase25a_notebook_sha_matches") is True)
chk("phase25a final refiner NOT used for OOF",
    b25a.get("final_refiner_used_for_oof") is False)
""")

# ==================================================================== §6
add_md("## §6 — Phase25B binding")
add_code("""
b25b = _j(AUD / "phase25c_phase25b_binding.json")
print(json.dumps({k: b25b[k] for k in ("phase25b_notebook_sha_matches",
      "matrix_sha_matches", "metadata_sha_matches", "schema_sha_matches",
      "phase25b_feature_values_used_for_label_generation")}, indent=1))
chk("phase25b notebook SHA exact", b25b.get("phase25b_notebook_sha_matches") is True)
chk("phase25b matrix SHA exact", b25b.get("matrix_sha_matches") is True)
chk("phase25b metadata SHA exact", b25b.get("metadata_sha_matches") is True)
chk("phase25b schema SHA exact", b25b.get("schema_sha_matches") is True)
chk("feature values NOT used for label generation",
    b25b.get("phase25b_feature_values_used_for_label_generation") is False)
""")

# ==================================================================== §7
add_md("""
## §7 — Stage ownership

| stage | role | owner |
|---|---|---|
| 25B | 202-D GT-free pre-refinement features | frozen |
| **25C** | **OOF paired refinement-gain labels** | **this phase** |
| 25D | benefit-router training + 16-D task embedding | NOT started |

The 16-D task embedding is trained **only** in Phase 25D. Phase 25C never instantiates the router.
""")
add_code("""
ent = _j(AUD / "phase25c_entry_gate.json")
print("entry gate:", ent.get("n_passed"), "/", ent.get("n_checks"), ent.get("verdict"))
chk("entry gate PASS", ent.get("verdict") == "PHASE25C_ENTRY_GATE_PASS")
chk("entry gate all_pass", ent.get("all_pass") is True)
""")

# ==================================================================== §8
add_md("## §8 — Population")
add_code("""
pop = pd.read_csv(TAB / "phase25c_population_accounting.csv")
display(sty(pop, "pop"))
_pop_n = dict(zip(pop["population"], pop["n"]))
chk("population rows = 4957", int(_pop_n["labeled_rows"]) == 4957)
chk("action_available = 4957", int(_pop_n["action_available"]) == 4957)
chk("action_unavailable = 0", int(_pop_n["action_unavailable"]) == 0)
""")

# ==================================================================== §9
add_md("## §9 — TEST / holdout / VAL locks")
add_code("""
tlock = _j(AUD / "phase25c_test_lock_audit.json")
print(json.dumps(tlock, indent=1)[:900])
chk("TEST reads = 0", tlock.get("test_reads") == 0)
chk("ROUTER_HOLDOUT reads = 0", tlock.get("holdout_reads") == 0)
chk("VAL reads = 0", tlock.get("val_reads") == 0)
""")

# ==================================================================== §10
add_md("## §10 — Outer-fold assignments")
add_code("""
assign = C.load_outer_fold_assignment()
from collections import Counter
cnt = Counter(assign.values())
print("outer-fold counts:", dict(sorted(cnt.items())))
chk("every DEV sample in exactly one outer fold", len(assign) == 4957)
chk("fold0 outer n = 1657", cnt[0] == 1657)
chk("fold1 outer n = 1652", cnt[1] == 1652)
chk("fold2 outer n = 1648", cnt[2] == 1648)
""")

# ==================================================================== §11
add_md("## §11 — Fold checkpoint inventory")
add_code("""
fb = pd.read_csv(TAB / "phase25c_fold_checkpoint_binding.csv")
display(sty(fb, "fb"))
fbj = _j(AUD / "phase25c_fold_checkpoint_binding.json")
chk("all fold checkpoints bound", fbj.get("all_fold_checkpoints_bound") is True)
chk("phase25a final NOT authorized for OOF",
    fbj.get("phase25a_final_refiner_not_authorized_confirmed") is True)
""")

# ==================================================================== §12
add_md("## §12 — Cross-fit leakage proof")
add_code("""
lf = _j(AUD / "phase25c_crossfit_leakage_audit.json")
print("verdict:", lf.get("verdict"))
print("violations:", lf.get("crossfit_leakage_violations"))
cov = pd.read_csv(TAB / "phase25c_crossfit_coverage.csv")
display(sty(cov, "cov"))
chk("cross-fit leakage = 0", lf.get("crossfit_leakage_violations") == 0)
chk("all in exactly one outer target",
    lf.get("samples_in_exactly_one_outer_target") == 4957)
chk("self-fit leak = 0", lf.get("samples_in_own_fit_population") == 0)
chk("self-early-stop leak = 0", lf.get("samples_in_own_early_stop_population") == 0)
""")

# ==================================================================== §13
add_md("## §13 — Canonical global-cache binding")
add_code("""
gc = _j(AUD / "phase25c_global_cache_binding.json")
print(json.dumps({k: gc[k] for k in ("global_model_forward_passes",
      "global_checkpoint_sha_matches", "prob512_dtype", "roi_proposal_threshold",
      "segmentation_output_threshold")}, indent=1))
chk("global forward passes = 0", gc.get("global_model_forward_passes") == 0)
chk("global checkpoint SHA matches", gc.get("global_checkpoint_sha_matches") is True)
chk("prob512 is float32", gc.get("prob512_dtype") == "float32")
""")

# ==================================================================== §14
add_md("## §14 — ROI-0.30 binding")
add_code("""
print("constants:", C.ROI_PROPOSAL_THRESHOLD, C.SEGMENTATION_OUTPUT_THRESHOLD)
chk("ROI proposal threshold = 0.30", abs(C.ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12)
chk("segmentation output threshold = 0.50",
    abs(C.SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12)
""")

# ==================================================================== §15
add_md("## §15 — Refiner inference execution binding")
add_code("""
ib = _j(AUD / "phase25c_refiner_inference_execution_binding.json")
print(json.dumps(ib.get("binding", {}), indent=1))
chk("binding classification PRE_EXECUTION_OPERATIONAL_BINDING",
    ib.get("classification") == "PRE_EXECUTION_OPERATIONAL_BINDING")
chk("binding selected before OOF outcomes",
    ib.get("selected_before_oof_outcomes") is True)
chk("FP32 inference", ib.get("binding", {}).get("inference_precision") == "float32")
chk("no TTA", ib.get("binding", {}).get("tta") is False)
chk("no checkpoint ensemble", ib.get("binding", {}).get("checkpoint_ensemble") is False)
""")

# ==================================================================== §16
add_md("## §16 — Crop / refiner input reconstruction")
add_code("""
ra = _j(AUD / "phase25c_fullfield_reconstruction_audit.json")
print(json.dumps(ra.get("geometry_identity_checks", {}), indent=1))
print("synthetic:", [(c["case"], c["outside_unchanged"], c["inside_replaced_exactly"])
                     for c in ra.get("synthetic_cases", [])])
chk("reconstruction verified", ra.get("verdict") == "PHASE25C_RECONSTRUCTION_VERIFIED")
chk("all outside unchanged", ra.get("all_outside_unchanged") is True)
chk("all inside replaced", ra.get("all_inside_replaced") is True)
""")

# ==================================================================== §17
add_md("## §17 — Full-field inverse transform")
add_code("""
print("inverse:", ra.get("inverse_transform"))
chk("geometry y-identity", ra["geometry_identity_checks"]["y1_plus_pad_equals_clip_y1"])
chk("geometry x-identity", ra["geometry_identity_checks"]["x1_plus_pad_equals_clip_x1"])
""")

# ==================================================================== §18
add_md("## §18 — Fusion rule")
add_code("""
print(ra.get("fusion_rule"))
chk("fusion is deterministic copy+replace (documented)",
    "replace" in ra.get("fusion_rule", ""))
""")

# ==================================================================== §19
add_md("## §19 — Segmentation threshold")
add_code("""
ts = _j(AUD / "phase25c_threshold_semantics_audit.json")
print(json.dumps(ts, indent=1)[:800])
chk("Dice uses segmentation threshold 0.50", ts.get("dice_uses_segmentation_threshold") is True)
chk("Dice does NOT use ROI threshold", ts.get("dice_uses_roi_threshold") is False)
""")

# ==================================================================== §20
add_md("## §20 — Dice metric binding")
add_code("""
mb = _j(AUD / "phase25c_metric_binding.json")
print(json.dumps({k: mb[k] for k in ("metric_source_file", "metric_function",
      "metric_source_sha256", "formula", "epsilon",
      "new_dice_formula_introduced")}, indent=1))
chk("canonical Dice bound", mb.get("verdict") == "PHASE25C_METRIC_BOUND")
chk("no new Dice formula", mb.get("new_dice_formula_introduced") is False)
chk("no conflicting metric definitions", mb.get("conflicting_metric_definitions_found") is False)
""")

# ==================================================================== §21-23
add_md("## §21–§23 — Fold OOF execution (fold0 / fold1 / fold2) and full coverage")
add_code("""
for k in (0, 1, 2):
    n = int((LAB["outer_fold"] == k).sum())
    print(f"fold{k}: OOF samples = {n}")
chk("fold0 coverage", int((LAB["outer_fold"] == 0).sum()) == 1657)
chk("fold1 coverage", int((LAB["outer_fold"] == 1).sum()) == 1652)
chk("fold2 coverage", int((LAB["outer_fold"] == 2).sum()) == 1648)
chk("full coverage = 4957", len(LAB) == 4957)
chk("no duplicate sample_id", LAB["sample_id"].duplicated().sum() == 0)
""")

# ==================================================================== §24
add_md("## §24 — Paired-label equation")
add_code("""
resid = np.abs(LAB["delta_dice"] - (LAB["candidate_refined_dice"] - LAB["global_dice"]))
print("max identity residual:", float(resid.max()))
chk("DeltaDice identity holds (< 1e-12)", float(resid.max()) <= 1e-12)
""")

# ==================================================================== §25
add_md("## §25 — Label-table integrity")
add_code("""
li = _j(AUD / "phase25c_label_integrity.json")
print(json.dumps({k: li[k] for k in ("rows", "duplicates", "nan", "inf",
      "router_holdout_ids_in_labels", "category_counts")}, indent=1))
chk("label integrity PASS", li.get("verdict") == "PHASE25C_LABEL_INTEGRITY_PASS")
chk("rows = 4957", li.get("rows") == 4957)
chk("no NaN", all(v == 0 for v in li.get("nan", {}).values()))
chk("no Inf", all(v == 0 for v in li.get("inf", {}).values()))
chk("no holdout ids", li.get("router_holdout_ids_in_labels") == 0)
""")

# ==================================================================== §26
add_md("## §26 — Beneficial / harmful / neutral definitions")
add_code("""
catc = pd.read_csv(TAB / "phase25c_gain_category_counts.csv")
display(sty(catc, "catc"))
print(f"BENEFICIAL >= +{C.BENEFICIAL_DELTA}; HARMFUL <= {C.HARMFUL_DELTA}; NEUTRAL otherwise")
tot = int(catc[["BENEFICIAL","NEUTRAL","HARMFUL"]].sum().sum())
chk("categories exhaustive (= 4957)", tot == 4957)
chk("each sample in exactly one category",
    len(LAB) == int((LAB.groupby("gain_category").size()).sum()))
""")

# ==================================================================== §27
add_md("## §27 — Overall gain summary")
add_code("""
ov = pd.read_csv(TAB / "phase25c_gain_summary_overall.csv")
display(sty(ov, "ov", {"mean": "{:.6f}", "median": "{:.6f}", "std": "{:.6f}"}))
print("Scientific gain magnitude is NOT a PASS criterion.")
""")
add_code("fig('p25c_delta_dice_distribution.png', 'DeltaDice distribution')")

# ==================================================================== §28
add_md("## §28 — Gain by domain")
add_code("""
bd = pd.read_csv(TAB / "phase25c_gain_summary_by_domain.csv")
display(sty(bd, "bd", {"mean": "{:.6f}", "median": "{:.6f}", "std": "{:.6f}"}))
""")
add_code("fig('p25c_delta_dice_by_domain.png', 'DeltaDice by domain')")
add_code("fig('p25c_gain_category_by_domain.png', 'Gain category by domain')")

# ==================================================================== §29
add_md("## §29 — Gain by fold")
add_code("""
bf = pd.read_csv(TAB / "phase25c_gain_summary_by_fold.csv")
display(sty(bf, "bf", {"mean": "{:.6f}", "median": "{:.6f}", "std": "{:.6f}"}))
""")
add_code("fig('p25c_delta_dice_by_outer_fold.png', 'DeltaDice by outer fold')")

# ==================================================================== §30
add_md("## §30 — Global vs candidate plot")
add_code("fig('p25c_global_vs_candidate_dice.png', 'Global vs candidate-refined Dice')")

# ==================================================================== §31
add_md("## §31 — Delta distribution vs global Dice")
add_code("fig('p25c_delta_vs_global_dice.png', 'DeltaDice vs global Dice')")

# ==================================================================== §32
add_md("## §32 — Fixed qualitative gallery")
add_code("""
print("Gallery selection is FIXED by a stable sample-id rule, independent of DeltaDice.")
""")
add_code("fig('p25c_fixed_oof_examples.png', 'Fixed OOF examples (RGB crop | p_global crop | GT crop)')")

# ==================================================================== §33
add_md("## §33 — Determinism audit")
add_code("""
det = _j(AUD / "phase25c_oof_determinism.json")
print(json.dumps({k: det[k] for k in ("subset_size", "replay_method",
      "max_candidate_dice_diff", "max_delta_dice_diff",
      "candidate_mask_mismatches", "verdict")}, indent=1))
chk("OOF determinism PASS", det.get("verdict") == "PHASE25C_OOF_DETERMINISM_PASS")
chk("subset size = 64", det.get("subset_size") == 64)
chk("0 mask mismatches", det.get("candidate_mask_mismatches") == 0)
""")
add_code("fig('p25c_crossfit_coverage.png', 'Cross-fit coverage')")

# ==================================================================== §34
add_md("## §34 — Phase25B join integrity")
add_code("""
ji = _j(AUD / "phase25c_phase25b_join_integrity.json")
print(json.dumps(ji, indent=1)[:900])
chk("join integrity PASS", ji.get("verdict") == "PHASE25C_JOIN_INTEGRITY_PASS")
chk("sample_id sets identical", ji.get("sample_id_sets_identical") is True)
chk("feature_row_index exact", ji.get("feature_row_index_mapping_exact") is True)
""")

# ==================================================================== §35
add_md("## §35 — No-router assertion")
add_code("""
sg = _j(AUD / "phase25c_scope_guard.json")
print(json.dumps(sg, indent=1)[:900])
chk("router NOT instantiated", sg.get("BARRBenefitRouterV1_instantiated") is False)
chk("router training runs = 0", sg.get("router_training_runs") == 0)
chk("router inference runs = 0", sg.get("router_inference_runs") == 0)
""")

# ==================================================================== §36
add_md("## §36 — No-task-embedding assertion")
add_code("""
chk("task embedding NOT instantiated", sg.get("task_embedding_instantiated") is False)
chk("task embedding training runs = 0", sg.get("task_embedding_training_runs") == 0)
chk("Huber loss training = 0", sg.get("Huber_loss_training") == 0)
""")

# ==================================================================== §37
add_md("## §37 — No-holdout assertion")
add_code("""
chk("holdout reads = 0", sg.get("holdout_reads") == 0)
chk("holdout feature reads = 0", sg.get("holdout_feature_reads") == 0)
""")

# ==================================================================== §38
add_md("## §38 — No-VAL assertion")
add_code("""
chk("VAL reads = 0", sg.get("val_reads") == 0)
chk("VAL dice = 0", sg.get("val_dice_computed") == 0)
""")

# ==================================================================== §39
add_md("## §39 — No-TEST assertion")
add_code("""
chk("TEST reads = 0", sg.get("test_reads") == 0)
chk("TEST inference = 0", sg.get("test_inference") == 0)
""")

# ==================================================================== §40
add_md("## §40 — Phase25D handoff")
add_code("""
ho = _j(AUD / "phase25c_phase25d_handoff_schema.json")
print(json.dumps(ho, indent=1)[:1200])
chk("handoff ready", ho.get("verdict") == "PHASE25C_PHASE25D_HANDOFF_READY")
chk("25C router_instantiated = false", ho.get("phase25c", {}).get("router_instantiated") is False)
chk("25C task_embedding_trained = false",
    ho.get("phase25c", {}).get("task_embedding_trained") is False)
""")

# ==================================================================== §41
add_md("## §41 — Final assertions")
add_code("""
n_pass = sum(1 for _, ok, _ in assertions if ok)
n_fail = sum(1 for _, ok, _ in assertions if not ok)
print(f"assertions: {n_pass} passed / {n_fail} failed / {len(assertions)} total")
for name, ok, detail in assertions:
    if not ok:
        print("  [FAIL]", name, detail)
chk("all assertions passed", n_fail == 0)
print("No router-training cells; no training curves; OOF labels only.")
""")

# ------------------------------------------------------------------ write
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p25c{_i:03d}"


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
        _outs = _c.get("outputs") if _c.cell_type == "code" else None
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

    # Address normalisation makes the build reproducible (object reprs carry heap
    # addresses). It MUST stay off binary/lossless payloads: a base64 PNG body can
    # legally contain the literal characters "0x" followed by >=6 hex-ish chars, and
    # rewriting those silently mutates the image (observed: a truncated tail / no
    # IEND chunk). Only text-ish MIME types + stream text are normalised.
    _ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
    _TEXTY = ("text/plain", "text/markdown", "text/html", "text/latex",
              "application/json", "text/csv")
    for _c in nb.cells:
        if _c.cell_type != "code":
            continue
        for _o in _c.get("outputs", []) or []:
            _d = _o.get("data")
            if isinstance(_d, dict):
                for _k, _v in list(_d.items()):
                    if _k not in _TEXTY:
                        continue
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
    for _c in nb.cells:
        if _c.cell_type != "code":
            continue
        for _o in _c.get("outputs", []) or []:
            if (_o.get("output_type") == "display_data"
                    and "image/png" in ((_o.get("data") or {}))):
                _pl = _o["data"]["image/png"]
                if isinstance(_pl, list):
                    _pl = "".join(_pl)
                _raw = base64.b64decode(_pl)
                assert _raw[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10]), "post-write PNG corrupt"
                assert _raw.rfind(b"IEND") >= len(_raw) - 12, "post-write PNG truncated"
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
