"""Phase 25A (CANONICAL RERUN) — canonical reviewer notebook builder.

Builds the CANONICAL Phase25A reviewer notebook for the ROI-0.30 execution, while
keeping the superseded ROI-0.50 execution visible (as provenance, explicitly
labelled noncanonical). The notebook must state prominently and with semantic
roles:

    ROI PROPOSAL THRESHOLD        = 0.30
    SEGMENTATION OUTPUT THRESHOLD = 0.50

Implementation strategy
-----------------------
The original ROI-0.50 builder is imported as a module and its ``cells`` list is
reused for everything that is threshold-independent. Only the threshold-bearing
cells are rewritten, and the threshold-adjudication sections are inserted. This
avoids duplicating ~1000 lines of governance prose that did not change.

Determinism: fixed cell ids (``p25aNNN``) + stripped ``metadata.execution`` +
coalesced stream outputs + fixed pandas Styler uuids + 0x-address normalisation.
Three consecutive builds must be byte-identical (no retraining between builds).

Usage:
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase25a_roi030_notebook.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


class _NoExecuteNotebookClient(NotebookClient):
    """Import-time stub: the ROI-0.50 builder writes+executes at module scope.

    We only want its assembled ``cells`` list, so execution is suppressed during
    the import step. The canonical notebook is executed by ``main()`` instead,
    against the canonical ROI-0.30 artifacts only. This also guarantees the
    import can never overwrite the superseded notebook with a partially-built
    (unpatched) version.
    """

    def execute(self, *a, **k):  # noqa: D102
        return self.nb

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
NB_PATH = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
           / "phase25a_dedicated_regional_refiner.ipynb")
BUILDER = ROOT / "scripts" / "notebooks" / "build_phase25a_notebook.py"
SUPERSEDED_NB_SHA = "7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f"

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))      # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))        # noqa: E731


def load_original_cells() -> list:
    """Import the ROI-0.50 builder and take its assembled ``cells`` list.

    The original builder executes at import time: its module body writes the
    notebook to a fixed ``NB_PATH`` and runs a live kernel. We must not let that
    happen, because it would (a) waste minutes of kernel time and (b) risk
    overwriting the superseded ROI-0.50 notebook with a *partially built*,
    unpatched intermediate.

    ``from nbclient import NotebookClient`` rebinds the name at the original
    builder's module scope when the body runs, so patching the module object
    afterwards is too late. Instead we load the source, substitute a no-op client
    and a discarded write, and exec the patched source in a private module dict.
    """
    src = BUILDER.read_text(encoding="utf-8")

    # 1. swap the executing client for a no-op (bound at import time)
    assert "from nbclient import NotebookClient" in src
    src = src.replace(
        "from nbclient import NotebookClient",
        "from nbclient import NotebookClient as _RealNotebookClient\n"
        "NotebookClient = _NOOP_NC",
    )
    # 2. neutralise every write the module body performs (both of them)
    assert src.count("nbformat.write(") == 2
    src = src.replace("nbformat.write(", "_noop_write(")

    mod = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location("p25a_original_builder", BUILDER))
    mod.__dict__["_NOOP_NC"] = _NoExecuteNotebookClient
    mod.__dict__["_noop_write"] = lambda *a, **k: None
    sys.modules["p25a_original_builder"] = mod
    exec(compile(src, str(BUILDER), "exec"), mod.__dict__)
    return list(mod.cells)


def find_cell(cells: list, needle: str, kind: str = "markdown") -> int:
    for i, c in enumerate(cells):
        if c.cell_type != kind:
            continue
        src = c.source if isinstance(c.source, str) else "".join(c.source)
        if needle in src:
            return i
    raise KeyError(f"cell not found ({kind}): {needle!r}")


def patch_source(cell, old: str, new: str) -> None:
    src = cell.source if isinstance(cell.source, str) else "".join(cell.source)
    assert old in src, f"patch target not found: {old!r}"
    cell.source = src.replace(old, new)


def main() -> int:
    print("Importing the ROI-0.50 builder to reuse its threshold-independent cells ...")
    cells = load_original_cells()
    print(f"reused {len(cells)} cells from the original builder")

    # ------------------------------------------------------------------ #
    # §0 root injection: repoint EXP / CKPT / CACHE at the CANONICAL trees
    # ------------------------------------------------------------------ #
    # Every later cell reads its artifacts through these four names, so this
    # patch must happen FIRST. Without it the notebook would silently read the
    # superseded ROI-0.50 experiment/checkpoint/cache trees.
    r = find_cell(cells, 'EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1"',
                  "code")
    patch_source(
        cells[r],
        'EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1"\n'
        'CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1"\n'
        'CACHE = ROOT / "data_cache" / "phase25a_global_cache"',
        '# CANONICAL ROI-0.30 trees (superseded ROI-0.50 trees are NOT read here)\n'
        'EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"\n'
        'CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"\n'
        'CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"\n'
        'SUPERSEDED_EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1"\n'
        'SUPERSEDED_CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1"\n'
        'print("CANONICAL EXP :", EXP.relative_to(ROOT))\n'
        'print("CANONICAL CKPT:", CKPT.relative_to(ROOT))\n'
        'print("CANONICAL CACHE:", CACHE.relative_to(ROOT))',
    )

    # ------------------------------------------------------------------ #
    # §6b tables + figure names -> canonical ROI-0.30 artifacts
    # ------------------------------------------------------------------ #
    # selected-epochs table (§ training history)
    s = find_cell(cells, 'sel = pd.read_csv(TAB / "phase25a_refiner_selected_epochs.csv")', "code")
    cells[s] = code("""
sel = pd.read_csv(TAB / "phase25a_roi030_refiner_selected_epochs.csv")
display(sty(sel, "p25a_roi030_selected_epochs", {"best_early_stop_loss": "{:.6f}",
                                                 "early_stop_dice_at_best": "{:.4f}"}))
fig("p25a_roi030_best_epoch_summary.png", "selected epoch per fold (ROI-0.30)")
""")

    # final-refit epoch rule -> canonical ROI-0.30 rule
    rr = find_cell(cells, 'rule = _j(AUD / "phase25a_final_refit_epoch_rule.json")', "code")
    patch_source(cells[rr], 'phase25a_final_refit_epoch_rule.json',
                 'phase25a_roi030_final_refit_epoch_rule.json')
    patch_source(cells[rr], 'print("uses holdout                :", rule.get("final_refit_uses_holdout"))',
                 'print("uses holdout                :", rule.get("holdout_used"))')
    patch_source(cells[rr], 'print("uses VAL                    :", rule.get("final_refit_uses_val"))',
                 'print("uses VAL                    :", rule.get("val_used"))')
    patch_source(cells[rr], 'print("uses TEST                   :", rule.get("final_refit_uses_test"))',
                 'print("uses TEST                   :", rule.get("test_used"))')
    patch_source(cells[rr],
                 'print("no early stopping in refit  :", rule.get("no_early_stopping_in_final_refit"))',
                 'print("no early stopping in refit  :", rule.get("early_stopping_in_final_refit") '
                 'is False)\nprint("ROI-0.50 median reused      :", rule.get("roi050_value_reused"))')

    # final refit curve + checkpoint listing
    patch_source(cells[find_cell(cells, "fig(\"p25a_final_refit_training_curve.png\"", "code")],
                 'fig("p25a_final_refit_training_curve.png", "R_psi_final refit curve")',
                 'fig("p25a_roi030_final_refit_training_curve.png", "R_psi_final refit curve (ROI-0.30)")')
    patch_source(cells[find_cell(cells, 'ck = CKPT / "final"', "code")],
                 'ck = CKPT / "final"', 'ck = CKPT / "final"  # canonical final.pt')

    # ------------------------------------------------------------------ #
    # §1 title: prepend the canonical / supersession banner
    # ------------------------------------------------------------------ #
    i = find_cell(cells, "# Phase 25A — Dedicated Crop-Trained Regional Refiner")
    cells[i] = md("""
# Phase 25A (CANONICAL) — Dedicated Crop-Trained Regional Refiner

## ⚠ ROI PROPOSAL THRESHOLD = **0.30**  ·  SEGMENTATION OUTPUT THRESHOLD = **0.50**

**Method:** `RA-MedFiLM-BARR` — Resource-Aware MedFiLM with Benefit-Aware Refinement Routing
**Architecture:** `ra_medfilm_barr_narrowed_v1_1`
**Module implemented and trained here:** `R_psi` (`BARRRegionalRefinerV1`) — **only this module**
**Classification of this notebook:** `CANONICAL_PHASE25A_AFTER_THRESHOLD_ADJUDICATION`

### Two thresholds, two semantic roles — never conflated

| threshold | value | semantic role | what it determines |
|---|---|---|---|
| **ROI PROPOSAL** foreground threshold | **0.30** | region proposal | predicted foreground → bbox existence → bbox geometry → `ACTION_AVAILABLE` vs `FORCED_SKIP` |
| **SEGMENTATION OUTPUT** threshold | **0.50** | segmentation / evaluation | final binary segmentation mask, Dice / IoU masks (inherited; **not** used for ROI) |

The ROI proposal threshold is the repository-authoritative Phase-24 v1.1 value
(`roi.predicted_foreground_threshold = 0.3`). The segmentation output threshold is the inherited
frozen decision threshold (`fusion.segmentation_threshold = 0.5`, source `INHERITED`).

### Why an earlier execution was superseded

A previously completed Phase25A execution trained the refiner with the ROI proposal threshold set
to **0.50**, having merely *reported* (not resolved) the conflict with the v1.1 exact spec. That
violates the Phase25A fail-closed rule — when the repository-authoritative v1.1 exact spec
disagrees, the run must STOP rather than silently bind a different value. It is preserved as:

**`NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50`** — superseded notebook SHA
`7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f`.
That execution is **not** used for any science: not for Phase25C, not for router labels, not for
holdout evaluation. It remains on disk as a protocol-deviation record only.

**Supersession is scientifically material.** The ROI threshold changes the predicted-foreground
bbox and hence the crop window: **4,265 of 4,957 development samples (86.0 %)** have different ROI
geometry at 0.30 than at 0.50. The refiner therefore had to be retrained from initialization.

This notebook trains the canonical ROI-0.30 refiner. It does **not** train the benefit router,
does **not** create paired-gain / `DeltaDice` labels, does **not** inspect `ROUTER_HOLDOUT`
outcomes, does **not** evaluate the 808-case VAL, and does **not** touch TEST.
""")

    # ------------------------------------------------------------------ #
    # §4 binding: add the adjudication pointer
    # ------------------------------------------------------------------ #
    j = find_cell(cells, 'b = _j(AUD / "phase25a_phase24_v1_1_binding.json")', "code")
    cells[j] = code("""
b = _j(AUD / "phase25a_phase24_v1_1_binding.json")
print("architecture_id          :", b.get("architecture_id"))
print("method_name              :", b.get("method_name"))
print("master_development_seed  :", b.get("master_development_seed"))
print("phase24 notebook sha256  :", b.get("phase24_notebook_sha256"))
print("phase24 exact spec sha256:", b.get("phase24_exact_spec_sha256"))
print("classification           :", b.get("classification"))
print()
roi = b.get("bound_roi", {})
print("bound ROI (adjudicated):")
for k in ("expansion_factor", "fractional_margin", "input_resolution",
          "roi_proposal_threshold", "segmentation_output_threshold",
          "predicted_foreground_threshold", "empty_prediction"):
    print(f"   {k:32s}: {roi.get(k)}")
print()
ref = b.get("bound_refiner", {})
print("bound refiner: name=%s in=%s out=%s params=%s ceiling=%s" % (
    ref.get("name"), ref.get("input_channels"), ref.get("output_channels"),
    ref.get("expected_parameters"), ref.get("hard_ceiling")))
print("active channels  :", ref.get("channels_active"))
print("rejected channels:", ref.get("channels_declared_rejected"))
print()
print("THRESHOLD ADJUDICATION (the two-role resolution)")
for d in b.get("discrepancies", []):
    print("  field                  :", d.get("field"))
    print("  v1.1 frozen value      :", d.get("phase24_v1_1_frozen_value"))
    print("  bound value NOW        :", d.get("bound_value_now"))
    print("  superseded bound value :", d.get("superseded_bound_value"))
    print("  segmentation output    :", d.get("segmentation_output_threshold"))
    print("  status                 :", d.get("status"))
    print("  adjudication status    :", d.get("adjudication_status"))
    print("  disagreement           :", d.get("disagreement"))
print()
print("The earlier 0.5 ROI binding was never repaired silently; it was REPORTED, then")
print("ADJUDICATED as a frozen-spec CLARIFICATION (phase24 science unchanged).")
""")
    cells.insert(j + 1, code("""
adj = _j(AUD / "phase24_phase25_roi_threshold_adjudication.json")
sup = _j(AUD / "phase25a_roi050_supersession.json")
print("THRESHOLD ADJUDICATION")
print("  classification                   :", adj.get("classification"))
print("  phase24_exact_spec_value         :", adj.get("phase24_exact_spec_value"))
print("  roi_proposal_threshold           :", adj.get("roi_proposal_threshold"))
print("  segmentation_output_threshold    :", adj.get("segmentation_output_threshold"))
print("  phase24_science_changed          :", adj.get("phase24_science_changed"))
print("  phase24_exact_spec_changed       :", adj.get("phase24_exact_spec_changed"))
print()
print("SUPERSEDED EXECUTION")
print("  classification                   :", sup.get("classification"))
print("  superseded threshold             :", sup.get("old_threshold"))
print("  superseded notebook sha256       :", sup.get("old_notebook_sha256"))
print("  scientific_use_allowed           :", sup.get("scientific_use_allowed"))
print("  allowed_role                     :", sup.get("allowed_role"))
"""))

    # ------------------------------------------------------------------ #
    # §6 cache provenance -> canonical ROI-0.30 cache
    # ------------------------------------------------------------------ #
    k = find_cell(cells, "prov = _j(AUD /", "code")
    cells[k] = code("""
prov = _j(AUD / "phase25a_roi030_cache_provenance.json")
print("classification                              :", prov.get("classification"))
print("population_n                                :", prov.get("population_n"))
print("roi_proposal_threshold                      :", prov.get("roi_proposal_threshold"))
print("roi_proposal_threshold_role                 :", prov.get("roi_proposal_threshold_role"))
print("segmentation_output_threshold               :", prov.get("segmentation_output_threshold"))
print("segmentation_output_threshold_role          :", prov.get("segmentation_output_threshold_role"))
print("roi_derivation_uses_segmentation_threshold  :",
      prov.get("roi_derivation_uses_segmentation_threshold"))
print("prior_noncanonical_threshold                :", prov.get("prior_noncanonical_threshold"))
print("prior_noncanonical_classification           :", prov.get("prior_noncanonical_classification"))
print("action_available_n                          :", prov.get("action_available_n"))
print("action_unavailable_global_empty_n           :", prov.get("action_unavailable_global_empty_n"))
print("assuming_zero_forced_skip_rejected          :",
      prov.get("assuming_zero_forced_skip_rejected"))
print("cache_root                                  :", prov.get("cache_root"))
print()
src = prov.get("probability_source", {})
print("probability source                :", src.get("source"))
print("global checkpoint sha256          :", src.get("global_checkpoint_sha256"))
print("global forward passes             :", src.get("global_forward_passes"))
print("persisted dtype                   :", src.get("persisted_dtype"))
print("threshold derivation precision    :", src.get("threshold_derivation_precision"))
print("reused float16 prob512            :", src.get("reused_float16_prob512"))
print()
print("NOTE: a decision at threshold 0.30 CANNOT be recovered losslessly from the")
print("pre-existing float16 prob512.npy (18-21 pixels/sample lie within 4 ULP of the")
print("threshold), so the canonical cache REPLAYS the frozen Phase-21 forward and")
print("persists prob512 as float32. '0 FORCED_SKIP' was RE-COMPUTED, not assumed.")
print()
man = _j(CACHE / "cache_manifest.json")
print("canonical cache roi_proposal_threshold      :", man.get("roi_proposal_threshold"))
print("canonical cache segmentation threshold      :", man.get("segmentation_output_threshold"))
print("canonical cache prob512 dtype               :", man.get("prob512_dtype"))
print("canonical cache by_domain                   :", json.dumps(man.get("by_domain")))
""")

    # ------------------------------------------------------------------ #
    # §7 action availability -> canonical table
    # ------------------------------------------------------------------ #
    m = find_cell(cells, 'aa = pd.read_csv(TAB / "phase25a_action_availability_by_domain.csv")',
                  "code")
    cells[m] = code("""
aa = pd.read_csv(TAB / "phase25a_roi030_action_availability_by_domain.csv")
display(sty(aa, "p25a_roi030_action_avail", {"availability_fraction": "{:.4f}"}))
print("total action-available:",
      int(aa[aa.domain == "ALL"]["action_available"].iloc[0])
      if (aa.domain == "ALL").any() else int(aa["action_available"].sum()))
print("NOTE: the 0-FORCED_SKIP outcome was RE-COMPUTED at threshold 0.30, not assumed.")
""")

    # ------------------------------------------------------------------ #
    # §8 ROI transform -> 0.30 with semantic roles
    # ------------------------------------------------------------------ #
    n = find_cell(cells, "## 8. Exact ROI transform and its ground-truth independence")
    cells[n] = md("""
## 8. Exact ROI transform and its ground-truth independence

threshold `p_global` at the **ROI PROPOSAL threshold 0.30** (lower-inclusive, float32) → tight
bbox → centre-preserving **1.50x** expansion (≡ margin 0.25) → clip to canvas → square zero pad →
crop RGB and `p_global` → resize to **256x256** (bilinear / bilinear / nearest).

The **segmentation output threshold 0.50 is NOT used anywhere in this transform** — it applies to
segmentation/evaluation masks only.

The transform has **no ground-truth input and no ground-truth code path**. The audit below proves
that changing GT cannot alter any ROI coordinate, the RGB crop, or the probability crop.
""")

    p = find_cell(cells, 'rt = _j(AUD / "phase25a_roi_transform_audit.json")', "code")
    cells[p] = code("""
from src.data.barr_roi import (ROI_PROPOSAL_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD,
                              THRESHOLD_SEMANTIC_ROLES)
print("ROI PROPOSAL threshold        :", ROI_PROPOSAL_THRESHOLD)
print("SEGMENTATION OUTPUT threshold :", SEGMENTATION_OUTPUT_THRESHOLD)
print("semantic roles                :", json.dumps(THRESHOLD_SEMANTIC_ROLES, indent=1))
print()
from src.data.barr_roi import assert_gt_cannot_alter_roi
import numpy as np
_p = np.zeros((512, 512), dtype=np.float32); _p[200:260, 200:260] = 0.9
_img = np.zeros((3, 512, 512), dtype=np.float32)
_g1 = np.zeros((512, 512), dtype=np.float32); _g1[100:120, 100:120] = 1
_g2 = np.zeros((512, 512), dtype=np.float32); _g2[400:470, 400:470] = 1
gi = assert_gt_cannot_alter_roi(_p, _img, _g1, _g2, ROI_PROPOSAL_THRESHOLD)
print("GT-independence (live check)  :", json.dumps(gi))
assert gi["passed"], "GT-independence FAILED"
rt = _j(AUD / "phase25a_roi_transform_audit.json")
print()
print("historical ROI-0.50 audit verdict :", rt.get("verdict"))
print("historical discrepancy status     :",
      json.dumps(rt.get("threshold_discrepancy", {}).get("status")))
print("discrepancy now RESOLVED by       : phase24_phase25_roi_threshold_adjudication.json")
""")

    # ------------------------------------------------------------------ #
    # threshold semantics audit section (new)
    # ------------------------------------------------------------------ #
    q = find_cell(cells, "## 9. `BARRRegionalRefinerV1` architecture")
    cells.insert(q, md("""
## 8b. Threshold semantics audit (fail-closed)

The audit verifies that the ROI proposal threshold is 0.30, that the segmentation output
threshold is 0.50, that no canonical ROI derivation uses 0.50, that no segmentation-output
threshold was changed to 0.30, and that no ambiguous bare `threshold` field remains. It fails
closed on any mismatch.
"""))
    cells.insert(q + 1, code("""
ts = _j(AUD / "phase25a_threshold_semantics_audit.json")
print("verdict                        :", ts.get("verdict"))
print("checks                         :", f"{ts.get('n_passed')}/{ts.get('n_checks')}")
print("roi proposal foreground thr    :", ts.get("roi_proposal_foreground_threshold"))
print("segmentation/fusion mask thr   :", ts.get("segmentation_fusion_mask_threshold"))
print("canonical ROI derivation 0.50  :", ts.get("canonical_roi_derivation_uses_0p50"))
print("segmentation thr changed 0.30  :", ts.get("canonical_segmentation_threshold_changed_to_0p30"))
print("ambiguous bare thr fields      :", ts.get("ambiguous_bare_threshold_fields_remaining"))
if ts.get("failed_checks"):
    print("FAILED:", ts["failed_checks"])
# The three notebook_* checks in this audit are only satisfiable AFTER this
# notebook has been written and executed, so they cannot be a precondition here.
# We assert that every FAILED check is one of those three notebook-dependent ones;
# the full audit is re-run (and required to PASS) by the notebook gate afterwards.
_nb_dependent = {"notebook_states_roi_proposal_0p30",
                 "notebook_states_segmentation_0p50",
                 "notebook_preserves_superseded_sha"}
_tz_failed = set(ts.get("failed_checks", []))
assert _tz_failed <= _nb_dependent, f"non-notebook threshold failure: {_tz_failed - _nb_dependent}"
print()
print("threshold-level checks PASS; notebook-dependent checks are verified post-build")
"""))

    # ------------------------------------------------------------------ #
    # §23 terminal cell: retarget the ROI-0.50 assertions to canonical 0.30
    # ------------------------------------------------------------------ #
    t = find_cell(cells, 'chk("bound threshold is 0.5"', "code")
    patch_source(
        cells[t],
        'chk("bound threshold is 0.5", b.get("bound_roi", {}).get("predicted_foreground_threshold") == 0.5)',
        'chk("bound ROI proposal threshold is 0.30",\n'
        '    b.get("bound_roi", {}).get("predicted_foreground_threshold") == 0.30)\n'
        'adj = _j(AUD / "phase24_phase25_roi_threshold_adjudication.json")\n'
        'chk("threshold adjudication frozen",\n'
        '    adj.get("verdict") == "PHASE24_PHASE25_ROI_THRESHOLD_ADJUDICATION_FROZEN")\n'
        'chk("adjudication is a clarification, not a science change",\n'
        '    adj.get("phase24_science_changed") is False\n'
        '    and adj.get("phase24_exact_spec_changed") is False)\n'
        'chk("ROI proposal role = 0.30", adj.get("roi_proposal_threshold") == 0.30)\n'
        'chk("segmentation output role = 0.50",\n'
        '    adj.get("segmentation_output_threshold") == 0.50)',
    )

    # 23b. refit-rule assertions must use the canonical ROI-0.30 artifact keys.
    #      NB: the §16 display cell also mentions the rule file, so locate the
    #      terminal cell by a marker unique to it, then patch inside that cell.
    t = find_cell(cells, 'print("PHASE25A_DEDICATED_REGIONAL_REFINER_COMPLETE',
                  "code")
    patch_source(cells[t], 'phase25a_final_refit_epoch_rule.json',
                 'phase25a_roi030_final_refit_epoch_rule.json')
    patch_source(
        cells[t],
        'chk("final refit epochs is integer median",\n'
        '    rule.get("final_refit_epochs") == sorted(rule.get("fold_best_epochs", {}).values())[1])',
        'chk("final refit epochs is integer median",\n'
        '    rule.get("final_refit_epochs") == sorted(rule.get("source_best_epochs", []))[1])\n'
        'chk("ROI-0.50 median was NOT reused", rule.get("roi050_value_reused") is False)',
    )
    patch_source(
        cells[t],
        'chk("holdout forbidden in final", rule.get("final_refit_uses_holdout") is False)',
        'chk("holdout forbidden in final", rule.get("holdout_used") is False)',
    )
    patch_source(
        cells[t],
        'chk("no early stopping in final", rule.get("no_early_stopping_in_final_refit") is True)',
        'chk("no early stopping in final", rule.get("early_stopping_in_final_refit") is False)',
    )

    # 23c. figure manifest -> canonical ROI-0.30 manifest with 9 figures.
    #      (anchor on the terminal cell: an earlier §-cell also names FIG_MANIFEST)
    patch_source(
        cells[t],
        'fm = _j(FIG / "FIG_MANIFEST.json")\n'
        'chk("8 required figures", len(fm.get("required", [])) == 8)',
        'fm = _j(FIG / "FIG_MANIFEST_ROI030.json")\n'
        'chk("9 required ROI-0.30 figures", len(fm.get("required", [])) == 9)',
    )

    # 23d. append canonical-specific terminal assertions before n_fail is computed.
    patch_source(
        cells[t],
        "n_fail = sum(1 for _, ok in assertions if not ok)",
        '# ---- canonical ROI-0.30 additions ----\n'
        'sup = _j(AUD / "phase25a_roi050_supersession.json")\n'
        'chk("superseded execution preserved", sup.get("preserved") is True)\n'
        'chk("superseded execution not scientifically usable",\n'
        '    sup.get("scientific_use_allowed") is False)\n'
        'chk("superseded notebook SHA recorded",\n'
        '    sup.get("old_notebook_sha256") == "'
        + SUPERSEDED_NB_SHA + '")\n'
        'chk("superseded artefacts never deleted",\n'
        '    sup.get("deleted_or_overwritten") is False)\n'
        '# canonical locks read from the ROI-0.30 audits (available at notebook-build time;\n'
        '# the final freeze is assembled AFTER the notebook, so it is not referenced here)\n'
        'lk30 = _j(AUD / "phase25a_roi030_no_outcome_leakage_audit.json")\n'
        'chk("canonical leakage PASS", lk30.get("verdict") == "PHASE25A_NO_OUTCOME_LEAKAGE_PASS")\n'
        'chk("canonical holdout outcomes not inspected",\n'
        '    lk30.get("router_holdout", {}).get("holdout_outcomes_inspected") is False)\n'
        'chk("canonical VAL not evaluated",\n'
        '    lk30.get("existing_val", {}).get("outcome_evaluation") == 0)\n'
        'chk("canonical paired-gain labels NOT created",\n'
        '    lk30.get("paired_gain_labels_created") is False)\n'
        'chk("canonical benefit router NOT trained",\n'
        '    lk30.get("benefit_router_training_runs") == 0)\n'
        'chk("canonical DeltaDice NOT computed", lk30.get("deltadice_computed") is False)\n'
        'tl30 = _j(AUD / "phase25a_roi030_test_lock_audit.json")\n'
        'chk("canonical TEST lock PASS",\n'
        '    tl30.get("verdict") == "PHASE25A_TEST_LOCK_PASS")\n'
        'chk("canonical TEST reads 0", tl30.get("test_reads") == 0)\n'
        'ci30 = _j(AUD / "phase25a_roi030_checkpoint_integrity.json")\n'
        'chk("canonical checkpoint integrity PASS",\n'
        '    ci30.get("verdict") == "PHASE25A_CHECKPOINT_INTEGRITY_PASS")\n'
        'rr30 = _j(AUD / "phase25a_roi030_final_refit_epoch_rule.json")\n'
        'chk("canonical refit epochs = integer median of ROI-0.30 folds",\n'
        '    rr30.get("final_refit_epochs") == 25)\n'
        'tz = _j(AUD / "phase25a_threshold_semantics_audit.json")\n'
        'chk("threshold semantics audit has no unknown failures",\n'
        '    set(tz.get("failed_checks", [])) <= {\n'
        '        "notebook_states_roi_proposal_0p30",\n'
        '        "notebook_states_segmentation_0p50",\n'
        '        "notebook_preserves_superseded_sha"})\n'
        '\n'
        'n_fail = sum(1 for _, ok in assertions if not ok)',
    )

    nb = nbformat.v4.new_notebook(cells=cells)
    for _i, _c in enumerate(nb.cells):
        _c["id"] = f"p25a{_i:03d}"
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
    monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
    imgs = sum(1 for c in code_cells for o in c.get("outputs", [])
               if "image/png" in (o.get("data", {}) or {}))
    sha_nb = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
    print(f"Cells: {len(nb.cells)} | markdown: "
          f"{sum(1 for c in nb.cells if c.cell_type == 'markdown')} | code: {len(code_cells)}")
    print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
    print("Monotonic exec counts:", "PASS" if monotonic else "FAIL")
    print("embedded PNG outputs:", imgs)
    print("Canonical notebook SHA256:", sha_nb)
    print("Superseded notebook SHA256:", SUPERSEDED_NB_SHA)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
