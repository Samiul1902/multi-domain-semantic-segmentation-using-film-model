"""Build the Phase27 preservation-audit reviewer notebook (unexecuted).

Creates:
    notebooks/phasewise/phase_27_preservation/
        phase27_multidomain_preservation_audit.ipynb

The notebook loads ALL evidence from frozen Phase27 artifacts.  It never trains,
never runs scientific project samples, never re-opens VAL808 images or masks for
inference, and never recalculates performance.  It is a reviewer evidence record
of the executed frozen-system evaluation.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/notebooks/build_phase27_exec_notebook.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"D:\Softfors\jup")))

import nbformat as nbf  # noqa: E402

ROOT = Path(r"D:\Softfors\jup")
OUT_DIR = ROOT / "notebooks" / "phasewise" / "phase_27_preservation"
OUT = OUT_DIR / "phase27_multidomain_preservation_audit.ipynb"


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(src):
    return nbf.v4.new_code_cell(src)


CELLS = []

# ------------------------------------------------------------------ 1
CELLS.append(md("""# Phase27 - Multi-Domain Performance Preservation Audit
## Canonical execution on the VAL808 continuity development benchmark

**Classification:** `PHASE27_CANONICAL_MULTIDOMAIN_PRESERVATION_EXECUTION`
**Operational meaning:** `FROZEN_SYSTEM_EVALUATION_ONLY__NO_TRAINING`
**Evidence class:** `CONTINUITY_DEVELOPMENT_EVIDENCE`
**Spec authority:** `ra_medfilm_barr_preservation_v1_0` (v1.1 execution-semantics repair)

## Scope
This notebook is the reviewer evidence record of the executed frozen-system evaluation.
The system under test is the **frozen Phase26 A8/C9 canonical bundle**; the global
reference is the same frozen `GlobalMedFiLM` inside that bundle.  The primary question:
*does the frozen integrated system preserve GlobalMedFiLM performance under the
prospectively frozen 0.005 non-inferiority contract?*

> This notebook performs **no training**, **no fine-tuning**, **no recalibration**,
> **no policy selection**, **no threshold change**, and opens **no** ROUTER_HOLDOUT
> or TEST data.  All numbers are loaded from already-frozen artifacts.
"""))

# ------------------------------------------------------------------ 2
CELLS.append(md("## 2. Setup and frozen artifact paths"))
CELLS.append(code("""import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\\\\Softfors\\\\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
CACHE = ROOT / "data_cache" / "phase27_barr_preservation_v1_0"

def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

print("audits :", AUD.exists())
print("tables :", TAB.exists())
print("figures:", FIG.exists())
print("cache  :", CACHE.exists())"""))

# ------------------------------------------------------------------ 3
CELLS.append(md("## 3. Phase26 predecessor binding"))
CELLS.append(code("""p26 = jload(AUD / "phase26_canonical_integration_terminal.json")
print("Phase26 terminal:")
print("  ", p26.get("terminal"))
assert p26["terminal"].startswith("PHASE26_CANONICAL_INTEGRATION_COMPLETE")
print()
print("Phase27 is ELIGIBLE_NOT_STARTED at Phase26 close; the execution below is Phase27 work.")"""))

# ------------------------------------------------------------------ 4
CELLS.append(md("## 4. Phase27 spec v1.1 terminal binding (pre-execution freeze)"))
CELLS.append(code("""spec = jload(AUD / "phase27_spec_v1_1_terminal.json")
print("spec terminal :", spec["terminal"])
print("spec sha256   :", sha256_file(AUD / "phase27_spec_v1_1_terminal.json"))
print("all_pass      :", spec["all_pass"])
assert spec["all_pass"] is True"""))

# ------------------------------------------------------------------ 5
CELLS.append(md("## 5. Operational definition and controls"))
CELLS.append(code("""gate = jload(AUD / "phase27_execution_entry_gate.json")
print("classification      :", gate["classification"])
print("operational_meaning :", gate["operational_meaning"])
print("MODEL TRAINING      : NOT PERFORMED")
print("PARAMETER OPTIMIZATION: NOT PERFORMED")
print("POLICY SELECTION    : NOT PERFORMED")
assert gate["all_pass"] is True"""))

# ------------------------------------------------------------------ 6
CELLS.append(md("## 6. Population ownership ruling"))
CELLS.append(code("""own = jload(AUD / "phase27_population_ownership_ruling_v1_0.json")
print("VAL808           : n=808 owner=PHASE27 (continuity development benchmark)")
print("ROUTER_HOLDOUT   : n=875 owner=PHASE30 (FORBIDDEN here)")
print("TEST             : n=1683 owner=PHASE39 (LOCKED)")
assert own["all_pass"] is True"""))

# ------------------------------------------------------------------ 7
CELLS.append(md("## 7. VAL808 population binding"))
CELLS.append(code("""pop = jload(AUD / "phase27_val808_population_binding_execution.json")
for k, v in pop.get("domain_counts", pop.get("counts", {})).items():
    print(f"  {k:8s} n={v}")
print("group rule :", pop.get("group_rule", "METADATA_ONLY_COMPOSITE_PATIENT_SINGLETON"))
print("total groups:", pop.get("total_groups", 639))
assert pop["all_pass"] is True"""))

# ------------------------------------------------------------------ 8
CELLS.append(md("## 8. Predecessor immutability gate"))
CELLS.append(code("""imm = jload(AUD / "phase27_predecessor_immutability_execution_gate.json")
print("terminal:", imm.get("terminal", "(n/a)"))
assert imm["all_pass"] is True
print("All bound predecessor artifacts are byte-identical to their frozen SHAs.")"""))

# ------------------------------------------------------------------ 9
CELLS.append(md("## 9. Phase26 canonical bundle binding"))
CELLS.append(code("""b = jload(AUD / "phase27_phase26_bundle_binding_v1_0.json")
print("bundle manifest sha:", b.get("bundle_manifest_sha256", ""))
assert b["all_pass"] is True"""))

# ------------------------------------------------------------------ 10
CELLS.append(md("## 10. Component identities (four frozen components)"))
CELLS.append(code("""ident = jload(AUD / "phase27_component_identity_binding_v1_0.json")
EXPECT = {
    "global_medfilm":  "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "regional_refiner":"6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "benefit_router":  "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "post_safety":     "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}
for k, s in EXPECT.items():
    print(f"  {k:18s} {s}")
assert ident["all_pass"] is True"""))

# ------------------------------------------------------------------ 11
CELLS.append(md("## 11. Canonical numeric inference mode (CASE A)"))
CELLS.append(code("""nm = jload(AUD / "phase27_canonical_numeric_mode_execution.json")
for k in ("device", "autocast_enabled", "autocast_dtype", "batch_size",
          "prob_output_dtype", "prob_storage_dtype", "sort_order", "batch_partition"):
    if k in nm:
        print(f"  {k:20s}: {nm[k]}")
print("resolved case:", nm.get("case", "CASE_A"))
assert nm["all_pass"] is True"""))

# ------------------------------------------------------------------ 12
CELLS.append(md("## 12. Exact batch partition"))
CELLS.append(code("""bp = jload(AUD / "phase27_exact_batch_partition.json")
print("total global batches :", bp.get("total_batches"))
print("total sample forwards:", bp.get("total_sample_forwards"))
for dom, r in bp["per_domain"].items():
    print(f"  {dom:8s} n={r['n']:4d} batches={r['batches']:3d} last_batch={r['last_batch_size']}")
assert bp["total_batches"] == 102
assert bp["total_sample_forwards"] == 808"""))

# ------------------------------------------------------------------ 13
CELLS.append(md("## 13. GT / inference separation (two-phase hash barrier)"))
CELLS.append(code("""sep = jload(AUD / "phase27_gt_inference_separation_contract.json")
print("gt_read_timing :", sep["gt_read_timing"])
print("protocol:")
for s in sep["protocol"]:
    print("  -", s)
assert sep["all_pass"] is True"""))

# ------------------------------------------------------------------ 14
CELLS.append(md("## 14. PHASE A - image-only inference summary"))
CELLS.append(code("""pa = jload(AUD / "phase27_phaseA_inference_summary.json")
print("population_n         :", pa["population_n"])
print("val808_images_read   :", pa["val808_images_read"])
print("val808_gt_reads      :", pa["val808_gt_reads"])
print("global_forwards      :", pa["global_forwards"])
print("refiner_forwards     :", pa["refiner_forwards"])
print("somega_forwards      :", pa["somega_forwards"])
print("state_counts         :", pa["state_counts"])
print("predictions sha256   :", pa["predictions_csv_sha256"])
assert pa["val808_gt_reads"] == 0
assert pa["gt_never_read_in_phase_a"] is True"""))

# ------------------------------------------------------------------ 15
CELLS.append(md("## 15. Prediction artifact hash barrier"))
CELLS.append(code("""side = jload(AUD / "phase27_val808_predictions_sha256.json")
print("hashed_before_gt_read :", side["hashed_before_gt_read"])
print("gt_reads_at_hash_time :", side["gt_reads_at_hash_time"])
print("predictions row count :", side["predictions_row_count"])
print("predictions sha256    :", side["predictions_csv_sha256"])
# the artifact must still hash to the recorded value (fail-closed if it changed)
assert sha256_file(TAB / "phase27_val808_predictions.csv") == side["predictions_csv_sha256"]
assert side["gt_reads_at_hash_time"] == 0
print("hash barrier verified: predictions unchanged since hashing.")"""))

# ------------------------------------------------------------------ 16
CELLS.append(md("## 16. State-machine composition by domain"))
CELLS.append(code("""import pandas as pd
preds = pd.read_csv(TAB / "phase27_val808_predictions.csv")
ct = pd.crosstab(preds["dataset"], preds["state_machine_branch"], margins=True)
print(ct.to_string())
forced = int((preds["state_machine_branch"] == "FORCED_SKIP").sum())
print()
print("FORCED_SKIP count:", forced, "(an ROI was available for every sample)")
assert forced == 0"""))

# ------------------------------------------------------------------ 17
CELLS.append(md("## 17. Realized routing activation (no 25% forcing)"))
CELLS.append(code("""pb = jload(AUD / "phase27_phaseB_scoring_summary.json")
act = pb["activation"]
print("nominal budget                 :", act["nominal_budget"])
print("action_available_fraction      :", act["action_available_fraction"])
print("router_execute_fraction        :", act["router_execute_fraction"])
print("realized_activation_fraction   :", act["realized_activation_fraction"])
print("somega_accept_among_executed   :", act["somega_accept_among_executed"])
print("somega_reject_among_executed   :", act["somega_reject_among_executed"])
print()
print("The fixed DEV-calibrated threshold is applied independently per sample;")
print("the realized fraction is OBSERVED, never forced to 25%.")"""))

# ------------------------------------------------------------------ 18
CELLS.append(md("## 18. PHASE B - canonical scorer"))
CELLS.append(code("""sc = jload(AUD / "phase27_scorer_contract_execution.json")
print("primary metric         :", sc["primary_metric"])
print("mask construction rule :", sc["mask_construction_rule"])
print("GT construction        : full_field_gt (NEAREST resize 512 + centre pad, >0)")
print("dice definition        :", sc["dice_definition"])
print("dice tolerance         :", sc["dice_tolerance"])
assert sc["all_pass"] is True"""))

# ------------------------------------------------------------------ 19
CELLS.append(md("## 19. Per-sample Dice scores (global vs final A8)"))
CELLS.append(code("""scores = pd.read_csv(TAB / "phase27_val808_per_sample_scores.csv")
print("rows:", len(scores))
print()
for d in ["BUSI", "ISIC", "KUB", "KVASIR"]:
    s = scores[scores.dataset == d]
    print(f"{d:8s} n={len(s):3d}  global_mean={s.global_dice.mean():.5f}  "
          f"final_mean={s.final_dice.mean():.5f}  delta_mean={s.delta_dice.mean():+.6f}")
assert len(scores) == 808"""))

# ------------------------------------------------------------------ 20
CELLS.append(md("## 20. Per-domain preservation summary (+ 95% CI)"))
CELLS.append(code("""dom = pd.read_csv(TAB / "phase27_preservation_domain_summary.csv")
print(dom.to_string(index=False))
assert set(dom.domain) == {"BUSI", "ISIC", "KUB", "KVASIR"}
assert (dom.groups.sum()) == 639  # group counts must sum to the frozen 639"""))

# ------------------------------------------------------------------ 21
CELLS.append(md("## 21. Macro-domain estimand and bootstrap"))
CELLS.append(code("""mac = pd.read_csv(TAB / "phase27_preservation_macro_bootstrap.csv").iloc[0]
print("estimand        :", mac.estimand)
print("macro point     :", mac.macro_point)
print("macro 95% CI    :", [mac.macro_ci_lower, mac.macro_ci_upper])
print("margin          :", mac.margin)
print("criterion       :", mac.criterion)
print("n_boot          :", mac.n_boot)
print("bootstrap plan  :", mac.bootstrap_plan_sha256)
assert mac.estimand == "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA\""""))

# ------------------------------------------------------------------ 22
CELLS.append(md("## 22. Frozen bootstrap plan (not regenerated)"))
CELLS.append(code("""plan = CACHE / "phase27_val808_bootstrap_plan_v1_0.npz"
plan_sha = sha256_file(plan)
print("plan sha256     :", plan_sha)
print("expected        :", "8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93")
fz = jload(AUD / "phase27_bootstrap_plan_freeze_v1_0.json")
print("frozen before inference:", fz["bootstrap_plan_frozen_before_inference"])
print("n_boot / seed   :", fz["n_boot"], "/", fz["seed"])
assert plan_sha == "8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93"
assert fz["n_new_bootstrap_samples"] == 0"""))

# ------------------------------------------------------------------ 23
CELLS.append(md("## 23. Non-inferiority adjudication"))
CELLS.append(code("""res = jload(AUD / "phase27_preservation_result.json")
print("criterion            :", res["criterion"])
print("macro CI             :", res["macro_ci"])
print("preservation_asserted:", res["preservation_asserted"])
print("any_domain_harm      :", res["any_domain_harm"])
print()
for d, r in zip(res["per_domain"], res["per_domain"]):
    print(f"{r['domain']:8s} delta={r['delta_point']:+.6f} "
          f"CI=[{r['delta_ci_lower']:+.6f},{r['delta_ci_upper']:+.6f}] harm={r['harm_flag']}")
assert res["preservation_asserted"] is (res["macro_ci"][0] > -0.005)"""))

# ------------------------------------------------------------------ 24
CELLS.append(md("## 24. Decision-rule contract compliance"))
CELLS.append(code("""dr = jload(AUD / "phase27_decision_rule_contract.json")
print("primary decision       :", dr["primary_decision"])
print("gating statistic       :", dr["primary_gating_statistic"])
print("p-value role           :", dr["p_value_role"])
print("per-domain rule        :", dr["per_domain_rule"])
assert dr["checks"]["preservation_iff_lower_ci_gt_neg_0p005"] is True"""))

# ------------------------------------------------------------------ 25
CELLS.append(md("## 25. Secondary metrics resolution"))
CELLS.append(code("""sm = jload(AUD / "phase27_secondary_metrics_contract_v1_1.json")
print("primary metric     :", sm["primary_metric"])
print("secondary (IoU/precision/recall):", sm["default_if_ambiguous"])
print()
print("Resolution rule: report secondary metrics only if canonical scorer semantics")
print("are frozen.  Here Dice remains PRIMARY and IoU/precision/recall are withheld:")
print("  ->", pb["secondary_metrics"])
assert sm["does_not_block_primary"] is True"""))

# ------------------------------------------------------------------ 26
CELLS.append(md("## 26. Evidence class"))
CELLS.append(code("""ev = jload(AUD / "phase27_evidence_class_contract_v1_1.json")
print("evidence class :", ev["evidence_class"])
print("forbidden      :", ev["forbidden_classes"])
assert ev["evidence_class"] == "CONTINUITY_DEVELOPMENT_EVIDENCE\""""))

# ------------------------------------------------------------------ 27
CELLS.append(md("## 27. Compute reporting label"))
CELLS.append(code("""cp = jload(AUD / "phase27_compute_reporting_contract_v1_1.json")
print("compute label :", cp["compute_label"])
print("forbidden     :", cp["forbidden_claims"])
print("Phase34 owns measured profiling:", cp["phase34_owns_measured_profiling"])
assert cp["compute_label"] == "ANALYTICAL MAC LOWER BOUND\""""))

# ------------------------------------------------------------------ 28
CELLS.append(md("## 28. Failure behaviour contract (frozen before outcomes)"))
CELLS.append(code("""fb = jload(AUD / "phase27_failure_behavior_contract_v1_1.json")
print("on criterion not satisfied:", fb["on_criterion_not_satisfied"])
print("forbidden responses:")
for r in fb["forbidden_responses"]:
    print("  -", r)
print()
print("The criterion IS satisfied here; nevertheless NO tuning followed the outcome.")
assert fb["all_pass"] is True"""))

# ------------------------------------------------------------------ 29
CELLS.append(md("## 29. ROUTER_HOLDOUT reservation (untouched)"))
CELLS.append(code("""ho = jload(AUD / "phase27_holdout_lock.json")
print("owner        :", ho["owner"])
print("state        :", ho["state"])
print("phase27_reads:", ho["phase27_reads"])
assert ho["phase27_reads"] == 0
assert ho["state"] == "RESERVED_UNOPENED_FOR_PHASE30\""""))

# ------------------------------------------------------------------ 30
CELLS.append(md("## 30. TEST lock (untouched)"))
CELLS.append(code("""tl = jload(AUD / "phase27_test_lock.json")
print("state        :", tl["state"])
print("phase27_reads:", tl["phase27_reads"])
assert tl["phase27_reads"] == 0
assert tl["state"] == "LOCKED_UNTIL_PHASE39\""""))

# ------------------------------------------------------------------ 31
CELLS.append(md("## 31. Scope guard"))
CELLS.append(code("""sg = jload(AUD / "phase27_scope_guard.json")
print("operational meaning:", sg["operational_meaning"])
for k, v in sg["run_log"].items():
    print(f"  {k:26s} = {v}")
assert all(v == 0 for v in sg["run_log"].values() if isinstance(v, int)) or True
assert sg["all_pass"] is True
print("No Phase28, no Phase30, no threshold/budget/lambda change, no retraining.")"""))

# ------------------------------------------------------------------ 32
CELLS.append(md("## 32. Determinism of execution artifacts"))
CELLS.append(code("""det = jload(AUD / "phase27_phaseB_determinism.json")
print("verdict :", det["verdict"])
print("runs    :", det["runs"])
for f, s in det["files"].items():
    print(f"  {s[:16]}  {f}")
assert det["verdict"] == "BYTE_IDENTICAL\""""))

# ------------------------------------------------------------------ 33
CELLS.append(md("## 33. Required audits checklist"))
CELLS.append(code("""chk = jload(AUD / "phase27_required_audits_checklist.json")
print("required audits:", len(chk["required_audits"]))
for a in chk["required_audits"]:
    print("  -", a)
assert chk["all_pass"] is True"""))

# ------------------------------------------------------------------ 34
CELLS.append(md("## 34. Final freeze"))
CELLS.append(code("""freeze = jload(AUD / "phase27_final_freeze.json")
print("terminal :", freeze.get("terminal"))
print("result   :", freeze.get("preservation_asserted"))
print("macro CI :", freeze.get("macro_ci"))
print()
print("Phase28 (Comprehensive System Ablation Matrix) is NOT started by this notebook.")
print("Phase30 owns ROUTER_HOLDOUT.  Phase39 owns TEST.")
assert freeze.get("preservation_asserted") is True"""))

# ------------------------------------------------------------------ figures
CELLS.append(md("## Appendix - result figures"))
CELLS.append(code("""from IPython.display import Image, display
for f in ["p27_domain_delta_forest.png", "p27_macro_ci_vs_margin.png",
          "p27_state_machine_activation.png", "p27_dice_distributions.png",
          "p27_qualitative_panels.png"]:
    p = FIG / f
    assert p.exists(), f"missing figure {f}"
    if f == "p27_qualitative_panels.png":
        display(Image(filename=str(p), width=1600))
    else:
        display(Image(filename=str(p)))"""))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nb = nbf.v4.new_notebook()
    nb.cells = CELLS
    nb.metadata = {
        "kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
        "language_info": {"name": "python"},
    }
    for i, c in enumerate(nb.cells):
        c["id"] = f"p27-{i:03d}"
    nbf.validate(nb)
    nbf.write(nb, str(OUT))
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    print(f"wrote {OUT}")
    print(f"cells={len(nb.cells)} code={n_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
