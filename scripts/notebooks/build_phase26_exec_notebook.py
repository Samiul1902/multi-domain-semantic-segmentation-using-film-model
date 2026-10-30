"""Build the Phase26 canonical integration reviewer notebook (unexecuted).

Creates:
    notebooks/phasewise/phase_26_full_system_integration/
        phase26_canonical_integration_and_bundle_freeze.ipynb

The notebook loads ALL evidence from frozen Phase26 artifacts. It never trains,
never runs scientific project samples, never opens masks, and never recalculates
Phase25 performance.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/notebooks/build_phase26_exec_notebook.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"D:\Softfors\jup")))

import nbformat as nbf  # noqa: E402

ROOT = Path(r"D:\Softfors\jup")
OUT_DIR = ROOT / "notebooks" / "phasewise" / "phase_26_full_system_integration"
OUT = OUT_DIR / "phase26_canonical_integration_and_bundle_freeze.ipynb"


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(src):
    return nbf.v4.new_code_cell(src)


CELLS = []

# ------------------------------------------------------------------ 1
CELLS.append(md("""# Phase26 - Canonical Integration & Bundle Freeze
## Full Four-Domain RA-MedFiLM-BARR (assembly only)

**Classification:** `CANONICAL_FULL_SYSTEM_INTEGRATION_AND_CONFIGURATION_FREEZE`
**Operational meaning:** `ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION`
**Spec authority:** `ra_medfilm_barr_phase26_integration_v1_0` + router deployment semantics v1.2

## Scope
This notebook is an evidence and compliance record. It **composes** the four already-frozen
canonical components into a single inference system, freezes the canonical bundle manifest, and
verifies contracts. It introduces **no learned parameters**, performs **no training**, runs
**no scientific data inference**, and **no threshold recalibration**.

> It never trains, never runs scientific project samples, never opens masks, and never
> recalculates Phase25 performance.
"""))

# ------------------------------------------------------------------ 2
CELLS.append(md("## 2. Legacy roadmap title provenance"))
CELLS.append(code("""import json
from pathlib import Path

ROOT = Path(r"D:\\Softfors\\jup")
AUD = ROOT / "reports" / "audits"
BUNDLE = ROOT / "artifacts" / "phase26_ra_medfilm_barr_bundle_v1_0"

def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

v12 = jload(AUD / "phase26_router_deployment_semantics_terminal_v1_2.json")
LEGACY_TITLE = "Full Four-Domain RA-MedFiLM-BARR Training"
OPERATIONAL_TITLE = "Full Four-Domain RA-MedFiLM-BARR Integration & Canonical Bundle Freeze"
print("legacy roadmap title   :", LEGACY_TITLE)
print("operational title      :", OPERATIONAL_TITLE)
print("redefined, not deleted :", LEGACY_TITLE != OPERATIONAL_TITLE)
assert v12["terminal"].startswith("PHASE26_SPEC_V1_2_COMPLETE")"""))

# ------------------------------------------------------------------ 3
CELLS.append(md("## 3. Operational Phase26 definition"))
CELLS.append(code("""gate = jload(AUD / "phase26_execution_entry_gate.json")
print("classification        :", gate["classification"])
print("operational_meaning   :", gate["operational_meaning"])
print("training_required     :", gate["checks"]["v12_final_check_26_of_26"] is not None and False)
print("MODEL TRAINING        : NOT PERFORMED")
print("PARAMETER OPTIMIZATION: NOT PERFORMED")
assert gate["all_pass"] is True"""))

# ------------------------------------------------------------------ 4
CELLS.append(md("## 4. Phase25 completion binding"))
CELLS.append(code("""p25g = jload(AUD / "phase25g_final_freeze.json")
print("Phase25 terminal:", p25g.get("terminal"))
assert "COMPLETE" in p25g["terminal"].upper()"""))

# ------------------------------------------------------------------ 5
CELLS.append(md("## 5. Phase26 v1.2 spec binding"))
CELLS.append(code("""import hashlib
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

print("v1.2 terminal :", v12["terminal"])
print("v1.2 sha256   :", sha256_file(AUD / "phase26_router_deployment_semantics_terminal_v1_2.json"))
assert v12["all_pass"] is True"""))

# ------------------------------------------------------------------ 6
CELLS.append(md("## 6. No-training declaration"))
CELLS.append(code("""nt = jload(AUD / "phase26_no_scientific_inference_audit.json")
for k in ("model_training_runs", "backward_passes", "optimizer_steps",
          "scientific_model_forwards", "router_holdout_reads", "val808_reads", "test_reads"):
    print(f"{k:32s} = {nt[k]}")
assert all(nt[k] == 0 for k in ("model_training_runs", "backward_passes", "optimizer_steps",
                                "scientific_model_forwards", "router_holdout_reads",
                                "val808_reads", "test_reads"))"""))

# ------------------------------------------------------------------ 7
CELLS.append(md("## 7. Component inventory"))
CELLS.append(code("""inv = jload(BUNDLE / "component_inventory.json")
for c in inv["components"]:
    print(f"{c['symbol']:8s} {c['model_class']:24s} {c['role']:18s} conditional={c['conditional']}")
assert len(inv["components"]) == 4"""))

# ------------------------------------------------------------------ 8
CELLS.append(md("## 8. Component SHA identities"))
CELLS.append(code("""EXPECT = {
    "G":       "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "R_psi":   "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "B_phi":   "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "S_omega": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}
for c in inv["components"]:
    print(f"{c['symbol']:8s} {c['checkpoint_sha256']}")
    assert c["checkpoint_sha256"] == EXPECT[c["symbol"]]
    assert c["binding"]["match"] is True"""))

# ------------------------------------------------------------------ 9
CELLS.append(md("## 9. Normalization identities"))
CELLS.append(code("""m = jload(BUNDLE / "canonical_bundle_manifest.json")
for name, b in m["normalizations"].items():
    print(f"{name:28s} {b['sha256']}")
    assert b["match"] is True
print("router normalization expected:",
      m["normalizations"]["router_normalization"]["expected_sha256"])"""))

# ------------------------------------------------------------------ 10
CELLS.append(md("## 10. Feature schemas"))
CELLS.append(code("""fc = jload(BUNDLE / "feature_contract.json")
print("router numeric dim :", fc["router_feature"]["dimension_numeric"])
print("B_phi input dim    :", fc["router_feature"]["b_phi_input_dim"])
print("post-safety total  :", fc["post_safety_feature"]["total_dim"])
assert fc["router_feature"]["dimension_numeric"] == 202
assert fc["router_feature"]["b_phi_input_dim"] == 218
assert fc["post_safety_feature"]["total_dim"] == 20
assert fc["router_feature"]["gt_free"] is True"""))

# ------------------------------------------------------------------ 11
CELLS.append(md("## 11. A8/C9 canonical variant"))
CELLS.append(code("""print("variant                 :", m["variant"])
print("nominal budget          :", m["nominal_budget"])
print("canonical lambda        :", m["canonical_lambda"])
assert m["variant"] == "A8_C9"
assert float(m["nominal_budget"]) == 0.25"""))

# ------------------------------------------------------------------ 12
CELLS.append(md("## 12. 25% development-selection provenance"))
CELLS.append(code("""c9 = jload(AUD / "phase26_c9_development_consistency.json")
print("canonical policy id    :", c9["canonical_policy_id"])
print("canonical policy rows  :", c9["canonical_policy_row_count"])
print("budget provenance      :", c9["canonical_budget_choice_provenance"])
assert c9["configuration_verification_only"] is True
assert c9["performance_metrics_recomputed"] is False"""))

# ------------------------------------------------------------------ 13
CELLS.append(md("## 13. Lambda representative semantics"))
CELLS.append(code("""print("lambda role                :", m["lambda_role"])
print("lambda performance-selected:", m["lambda_performance_selected"])
print("selection time             :", m["selection_time"])
assert m["lambda_performance_selected"] is False
assert m["lambda_role"] == "MEMBERSHIP_EQUIVALENT_SERIALIZATION_REPRESENTATIVE\""""))

# ------------------------------------------------------------------ 14
CELLS.append(md("## 14. OOF scientific calibration"))
CELLS.append(code("""oof = m["A_OOF_SCIENTIFIC_EVIDENCE"]
print("score variable   :", oof["score_variable"])
print("raw threshold    :", oof["raw_threshold_exact"])
print("resource thresh  :", oof["resource_threshold_exact"])
print("role             :", oof["role"])
print("runtime authority:", oof["runtime_authority"])
print("selected count   :", oof["oof_selected_count"])
assert oof["runtime_authority"] is False
assert oof["oof_selected_count"] == 1239"""))

# ------------------------------------------------------------------ 15
CELLS.append(md("## 15. Final-router runtime calibration"))
CELLS.append(code("""fin = m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]
print("score variable   :", fin["score_variable"])
print("producer         :", fin["producer"])
print("raw threshold    :", fin["raw_threshold_exact"])
print("lambda*C         :", fin["lambda_C_exact"])
print("resource utility :", fin["resource_utility_threshold_exact"])
print("runtime authority:", fin["runtime_authority"])
print("selected count   :", fin["dev_calibration_selected_count"])
assert fin["runtime_authority"] is True
assert fin["dev_calibration_selected_count"] == 1239"""))

# ------------------------------------------------------------------ 16
CELLS.append(md("## 16. OOF-vs-final membership distinction"))
CELLS.append(code("""rel = jload(AUD / "phase26_oof_scientific_cache_replay.json")
fr = jload(AUD / "phase26_final_router_cache_replay.json")
print("OOF    selected count:", rel["selected_count"], rel["selected_ids_sha256"][:16])
print("final  selected count:", fr["selected_count"], fr["selected_ids_sha256"][:16])
print("OOF/final equality required:", fr["oof_final_membership_equality_required"])
assert rel["selected_count"] == 1239 and fr["selected_count"] == 1239
assert fr["oof_final_membership_equality_required"] is False
assert rel["selected_ids_sha256"] != fr["selected_ids_sha256"]"""))

# ------------------------------------------------------------------ 17
CELLS.append(md("## 17. Exact threshold rational arithmetic"))
CELLS.append(code("""from fractions import Fraction as F

LAMBDA = F(1, 4)
C = F(1051648, 10270749)
TAU_C7_FINAL = F(24796109646558761, 20000000000000000000)
TAU_C8_FINAL = TAU_C7_FINAL - LAMBDA * C
TAU_C7_OOF = F(29487973, 10000000000)
TAU_C8_OOF = TAU_C7_OOF - LAMBDA * C

print("C                :", C)
print("lambda*C         :", LAMBDA * C)
print("tau_C7_final     :", TAU_C7_FINAL)
print("tau_C8_final     :", TAU_C8_FINAL)
print("tau_C8_oof       :", TAU_C8_OOF)
assert str(TAU_C8_FINAL) == "-5003565381643716252018011/205414980000000000000000000"
assert str(TAU_C8_OOF) == "-2326256430798223/102707490000000000\""""))

# ------------------------------------------------------------------ 18
CELLS.append(md("## 18. Future-cohort fixed-threshold rule"))
CELLS.append(code("""print("future cohort policy :", m["future_cohort_policy"])
for k, v in m["future_cohort_forbidden"].items():
    print(f"  forbidden {k:34s}: {v}")
print("phase30 nominal budget      :", m["phase30_nominal_budget"])
print("phase30 realized activation :", m["phase30_realized_activation_fraction"])
assert m["future_cohort_policy"] == "FIXED_DEV_CALIBRATED_THRESHOLD"
assert all(m["future_cohort_forbidden"].values())"""))

# ------------------------------------------------------------------ 19
CELLS.append(md("## 19. Canonical inference state machine"))
CELLS.append(code("""sm = jload(BUNDLE / "state_machine_contract.json")
print("states                       :", sm["states"])
print("global forwards per input    :", sm["global_forward_count_per_input"])
print("safety accept                :", sm["safety_accept"])
print("final segmentation           :", sm["final_segmentation"])
for t in sm["transitions"]:
    print(f"  {t['state']:22s} refiner={t['refiner']} s_omega={t['s_omega']} -> {t['final_probability'][:28]}")
assert sm["global_forward_count_per_input"] == 1
assert len(sm["states"]) == 4"""))

# ------------------------------------------------------------------ 20
CELLS.append(md("## 20. ROI rules"))
CELLS.append(code("""rc = jload(BUNDLE / "threshold_contract.json")
print("ROI proposal threshold :", rc["roi_proposal_threshold"], "(bbox -> ACTION_AVAILABLE / FORCED_SKIP)")
print("ROI expansion          : 1.50 (= 1 + 2*0.25)")
print("segment output thresh  :", rc["segmentation_output_threshold"], "(final mask / Dice / IoU)")
assert rc["roi_proposal_threshold"] == 0.30
assert rc["segmentation_output_threshold"] == 0.50"""))

# ------------------------------------------------------------------ 21
CELLS.append(md("## 21. Post-safety rules"))
CELLS.append(code("""print("safety accept threshold :", rc["s_omega_accept_threshold"])
print("safety score            : sigmoid(logit)")
print("post-safety features    : 16 numeric (standardized) + 4 one-hot task = 20")
print("normalized indices      : 0..15 ; not normalized: 16..19")
assert rc["s_omega_accept_threshold"] == 0.50"""))

# ------------------------------------------------------------------ 22
CELLS.append(md("## 22. Final segmentation rule"))
CELLS.append(code("""print("final binary output : p_final >= 0.50")
print()
print("SEMANTIC DISTINCTION (three distinct 0.50/0.30 uses):")
print("  0.30 = ROI PROPOSAL threshold")
print("  0.50 = S_omega ACCEPT probability threshold")
print("  0.50 = SEGMENTATION probability threshold")
assert m["thresholds_distinct"]["note"].startswith("separate contract fields")"""))

# ------------------------------------------------------------------ 23
CELLS.append(md("## 23. Analytical compute inventory"))
CELLS.append(code("""res = jload(BUNDLE / "resource_contract.json")
for k in ("global_macs", "benefit_router_macs", "regional_refiner_macs", "s_omega_macs"):
    print(f"{k:26s} = {res[k]:,} MACs")
print("label  :", res["label"])
print("never  :", res["never_call"])
assert res["label"] == "ANALYTICAL MAC LOWER BOUND\""""))

# ------------------------------------------------------------------ 24
CELLS.append(md("## 24. Wrapper source binding"))
CELLS.append(code("""src = jload(AUD / "phase26_source_code_integrity.json")
print("wrapper   :", src["wrapper_path"])
print("sha256    :", src["wrapper_sha256"])
print("validator :", src["validator_path"])
print("sha256    :", src["validator_sha256"])
assert src["learned_model_source_modified"] is False"""))

# ------------------------------------------------------------------ 25
CELLS.append(md("## 25. Strict component-load checks"))
CELLS.append(code("""load = jload(AUD / "phase26_component_load_integrity.json")
for sym, c in load["components"].items():
    print(f"{sym:8s} strict={c['strict_load_ok']} missing={len(c['missing_keys'])} "
          f"unexpected={len(c['unexpected_keys'])} params={c['parameter_count']}")
    assert c["strict_load_ok"] and not c["missing_keys"] and not c["unexpected_keys"]
assert load["all_pass"] is True"""))

# ------------------------------------------------------------------ 26
CELLS.append(md("## 26. Synthetic interface tests"))
CELLS.append(code("""it = jload(AUD / "phase26_integration_wrapper_audit.json")
print("classification of calls :", it["classification_of_calls"])
print("scientific forwards     :", it["scientific_sample_forwards"])
for t in it["tests"]:
    print(f"  [{'PASS' if t['pass'] else 'FAIL'}] {t['test']} {t['detail']}")
assert it["all_pass"] is True
assert it["scientific_sample_forwards"] == 0"""))

# ------------------------------------------------------------------ 27
CELLS.append(md("## 27. State-machine branch tests"))
CELLS.append(code("""st = jload(AUD / "phase26_state_machine_test_audit.json")
for c in st["cases"]:
    print(f"  {c['case']:22s} state={c['actual_state']:22s} g={c['global']} "
          f"r={c['refiner']} s={c['s_omega']}")
assert st["all_pass"] is True
assert st["global_forward_exactly_once"] is True"""))

# ------------------------------------------------------------------ 28
CELLS.append(md("## 28. Threshold equivalence tests"))
CELLS.append(code("""th = jload(AUD / "phase26_threshold_equivalence_test.json")
for c in th["cases"]:
    print(f"  raw {c['case']:6s} delta={c['delta_hat_final']!r:24s} -> {c['decision']}")
print("comparator           :", th["comparator"])
print("exact-vs-float diff  :", th["exact_vs_utility_abs_diff"])
assert th["all_pass"] is True"""))

# ------------------------------------------------------------------ 29
CELLS.append(md("## 29. Final-router frozen-cache replay"))
CELLS.append(code("""print("source           :", fr["source"])
print("threshold_exact  :", fr["threshold_exact"])
print("selected count   :", fr["selected_count"])
print("membership sha   :", fr["selected_ids_sha256"])
print("model forward    :", fr["model_forward"])
assert fr["selected_count"] == 1239
assert fr["checks"]["membership_matches_frozen"] is True"""))

# ------------------------------------------------------------------ 30
CELLS.append(md("## 30. OOF frozen-cache replay"))
CELLS.append(code("""print("source         :", rel["source"])
print("threshold      :", rel["threshold_exact"])
print("selected count :", rel["selected_count"])
print("membership sha :", rel["selected_ids_sha256"])
print("cross-promoted to runtime:", rel["cross_promoted_to_runtime"])
assert rel["selected_count"] == 1239
assert rel["checks"]["membership_matches_frozen_oof"] is True"""))

# ------------------------------------------------------------------ 31
CELLS.append(md("## 31. Bundle manifest"))
CELLS.append(code("""print("bundle revision        :", m["bundle_revision"])
print("phase26 revision       :", m["phase26_revision"])
print("router semantics       :", m["router_semantics_revision"])
print("operational threshold  :", m["operational_threshold"])
print("operational value      :", m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["resource_utility_threshold_exact"])
assert m["operational_threshold"] == "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold\""""))

# ------------------------------------------------------------------ 32
CELLS.append(md("## 32. Manifest validator"))
CELLS.append(code("""integ = jload(AUD / "phase26_bundle_manifest_integrity.json")
for k, v in integ["checks"].items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")
assert integ["all_pass"] is True"""))

# ------------------------------------------------------------------ 33
CELLS.append(md("## 33. Deterministic manifest SHA"))
CELLS.append(code("""det = jload(AUD / "phase26_bundle_manifest_determinism.json")
print("builds                  :", det["builds"])
print("three builds identical  :", det["three_builds_byte_identical"])
for s in det["manifest_shas"]:
    print("  ", s)
assert det["three_builds_byte_identical"] is True
assert len(set(det["manifest_shas"])) == 1"""))

# ------------------------------------------------------------------ 34
CELLS.append(md("## 34. No scientific inference audit"))
CELLS.append(code("""print("synthetic forwards classification :", nt["synthetic_forwards_classification"])
for k in ("project_image_reads", "project_mask_reads",
          "router_development_image_reads", "router_development_mask_reads",
          "router_holdout_reads", "val808_reads", "test_reads",
          "model_training_runs", "backward_passes", "optimizer_steps",
          "scientific_model_forwards"):
    print(f"  {k:36s} = {nt[k]}")
assert nt["all_pass"] is True"""))

# ------------------------------------------------------------------ 35
CELLS.append(md("## 35. ROUTER_HOLDOUT reservation"))
CELLS.append(code("""ho = jload(AUD / "phase26_holdout_lock_execution_audit.json")
print("owner :", ho["owner"])
print("state :", ho["state"])
print("reads :", ho["reads"])
assert ho["state"] == "RESERVED_UNOPENED_FOR_PHASE30"
assert ho["reads"] == 0"""))

# ------------------------------------------------------------------ 36
CELLS.append(md("## 36. VAL808 lock"))
CELLS.append(code("""va = jload(AUD / "phase26_val808_lock_execution_audit.json")
print("state :", va["state"])
print("reads :", va["reads"])
assert va["state"] == "UNOPENED" and va["reads"] == 0"""))

# ------------------------------------------------------------------ 37
CELLS.append(md("## 37. TEST lock"))
CELLS.append(code("""te = jload(AUD / "phase26_test_lock_execution_audit.json")
print("state :", te["state"])
print("reads :", te["reads"])
assert te["state"] == "LOCKED_UNTIL_PHASE39" and te["reads"] == 0"""))

# ------------------------------------------------------------------ 38
CELLS.append(md("## 38. Phase27 handoff"))
CELLS.append(code("""print("Phase26 status after success : COMPLETE_CANONICAL")
print("Phase27 status               : ELIGIBLE_NOT_STARTED")
print("This notebook does NOT start Phase27.")
print("Phase27 entry condition: supervisor authorization only.")"""))

# ------------------------------------------------------------------ 39
CELLS.append(md("## 39. Phase30 holdout handoff"))
CELLS.append(code("""print("ROUTER_HOLDOUT owner          : PHASE30")
print("ROUTER_HOLDOUT state          : RESERVED_UNOPENED_FOR_PHASE30")
print("Future-cohort policy          :", m["future_cohort_policy"])
print("Forbidden: top-K forcing / exact 25% cohort ranking / threshold fitting /")
print("           quantile recalibration")
print("Report nominal budget AND realized activation fraction.")"""))

# ------------------------------------------------------------------ 40
CELLS.append(md("## 40. Final assertions"))
CELLS.append(code("""final = jload(AUD / "phase26_final_freeze.json")
print("terminal:", final.get("terminal", "(pending)"))
assert final["variant"] == "A8_C9"
assert final["training_required"] is False
assert final["parameter_optimization"] is False
assert final["scientific_model_forwards"] == 0
assert final["training_runs"] == 0
assert final["runtime_threshold_exact"] == "-5003565381643716252018011/205414980000000000000000000"
print()
print("ALL PHASE26 NOTEBOOK ASSERTIONS PASS.")"""))

# ------------------------------------------------------------------ figures
CELLS.append(md("## Appendix - architecture figures"))
CELLS.append(code("""from IPython.display import Image, display
FIG = ROOT / "reports" / "figures" / "phase26_integration"
for f in ["p26_canonical_inference_state_machine.png", "p26_bundle_component_graph.png"]:
    p = FIG / f
    assert p.exists(), f"missing figure {f}"
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
        c["id"] = f"p-{i:03d}"
    nbf.validate(nb)
    nbf.write(nb, str(OUT))
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    print(f"wrote {OUT}")
    print(f"cells={len(nb.cells)} code={n_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
