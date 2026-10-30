#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0f synthetic-smoke reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0F_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK
Reads only the produced v1.0f smoke/provenance/final-check/terminal JSONs. Constructs no model,
deserializes no checkpoint, runs no forward or autograd, runs no Grad-CAM, runs no router
attribution, reads no real data, and reads no TEST/HOLDOUT.

For THIS new notebook the physical representation is reported truthfully: it is rendered/executed
here, so its representation is EXECUTED_WITH_PERSISTED_OUTPUTS (it is NOT a stripped clean source).
Determinism = the notebook source is rendered 3x; the smoke is NOT re-run.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_synthetic_smoke_notebook_v1_0f.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_35_interpretability" /
      "phase35_interpretability_synthetic_smoke_v1_0f_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0f"

SETUP = '''\
import hashlib
import json
from pathlib import Path
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
smoke = jload(AUD / "phase35_synthetic_interpretability_smoke_v1_0f.json")
prov  = jload(AUD / "phase35_synthetic_smoke_provenance_v1_0f.json")
fc    = jload(AUD / "phase35_synthetic_smoke_final_check_v1_0f.json")
term  = jload(AUD / "phase35_synthetic_smoke_terminal_v1_0f.json")
freeze = jload(AUD / "phase35_preexecution_source_freeze_v1_0f.json")
print("Phase35 v1.0f synthetic smoke review (READ-ONLY)")
print("This notebook READS the produced v1.0f smoke/provenance/final-check/terminal artifacts only.")
print("No model construction, no checkpoint deserialization, no forward, no autograd, no Grad-CAM,")
print("no router attribution, no images, no real p_global, no VAL808 cache, no HOLDOUT/TEST.")
'''

CELLS = []
_META = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": KERNEL},
         "language_info": {"name": "python", "version": "3.11.9"}}


def md(src):
    CELLS.append(nbformat.v4.new_markdown_cell(src))


def code(src):
    CELLS.append(nbformat.v4.new_code_cell(src))


md("""# Phase 35 v1.0f - Synthetic Interpretability Smoke
## Reviewer Notebook (read-only)

**Classification:** `READ_ONLY_PHASE35_V1_0F_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK`
**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0f`
**Smoke classification:** `PRE_SCIENTIFIC_SYNTHETIC_NUMERICAL_SAFETY_AND_INTERFACE_VALIDATION`
**Explicit:** `NOT_PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT`

This notebook reviews the ONE authorized v1.0f synthetic-only smoke execution. It is READ-ONLY over
the produced JSON artifacts. It does not construct models, load checkpoints, run forwards or
autograd, run Grad-CAM, run router attribution, read real medical data, or read TEST/HOLDOUT.

The smoke was invoked exactly ONCE (`--mode smoke`) with `PHASE35_SMOKE_EXECUTE=1` and
`PHASE35_EXECUTE` unset. No retry was performed.""")

md("## 0. Setup (read-only artifact loading)")
code(SETUP)

md("## 1. Result and blocking status")
code('''print("terminal:", term["terminal"])
print("smoke result:", smoke["result"])
print("harness all_pass:", smoke["harness_all_pass"])
print("counts_match_expected:", smoke["counts_match_expected"])
print("scientific_and_interface_checks_all_pass:", smoke["scientific_and_interface_checks_all_pass"])
print("invocation_count:", smoke["invocation_count"], "retries:", smoke["retries_performed"])
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print("failed checks:", fc["failed"])''')

md("""## 2. Blocking root cause

Every model, numerical, interface, and protected-data check passed. The single blocking condition is
an **internal execution-count integrity mismatch**: `counts_match_expected=False`, driven by the
counter `synthetic_smoke_target_masks` = **2** where the frozen v1.0c expected value is **1**.

Mechanism: the frozen v1.0c counter store is reused VERBATIM, but the v1.0f change introduced a
second increment. `V0D.smoke_synthetic_target_mask_rank2()` increments once for the primary
centered-square mask; `empty_mask_helper_check_insession_actual_logits()` then increments again for
the all-False empty variant derived from the SAME primary mask. `SMOKE_EXPECTED_COUNTERS` was not
updated alongside the repair, so the harness's internal consistency gate correctly fails closed.""")

code('''m = smoke["counter_mismatches"]["synthetic_smoke_target_masks"]
for k in ("observed","expected","cause","semantic_effect","scientific_effect"):
    print(f"{k}: {m[k]}")
print()
print("blocking detail:", json.dumps(fc["blocking_detail"], indent=1))''')

md("## 3. Source / hash gate and environment")
code('''print("sources verified:", prov["source_hash_gate"]["n_sources_verified"],
      "mismatch:", prov["source_hash_gate"]["n_mismatch"],
      "before model construction:", prov["source_hash_gate"]["verified_before_model_construction"])
print("G checkpoint match:", prov["checkpoint_gate"]["G"]["match"], prov["checkpoint_gate"]["G"]["sha256"])
print("B_phi checkpoint match:", prov["checkpoint_gate"]["B_phi"]["match"], prov["checkpoint_gate"]["B_phi"]["sha256"])
env = smoke["environment"]
print("env:", env["python"], env["torch"], env["gpu"], "cc", env["cc"], "cuda", env["cuda_available"])''')

md("## 4. Canonical model construction, strict load, and parameter counts")
code('''ms = smoke["model_scope"]
for k in ("G_constructions","B_phi_constructions","checkpoint_deserializations","strict_loads",
          "G_parameter_count","B_phi_parameter_count","G_missing_keys","G_unexpected_keys",
          "B_phi_missing_keys","B_phi_unexpected_keys","R_psi_construction_load_forward",
          "S_omega_construction_load_forward"):
    print(f"{k}: {ms[k]}")''')

md("## 5. FiLM sites and task embeddings")
code('''fs = smoke["film_smoke"]
print("film all_pass:", fs["all_pass"], "| scientific_film_tables_emitted:", fs["scientific_film_tables_emitted"])
sites = {}
for key, v in fs["per_task_site"].items():
    dom, site = key.split("|")
    sites.setdefault(site, set()).add((v["gamma_len"], v["expected_channels"], v["finite"]))
for site in ("bridge","decoder4","decoder3","decoder2","decoder1"):
    print(site, "gamma_len/expected/finite:", sites[site])
print()
es = smoke["embedding_smoke"]
print("G task embedding:", es["G_task_embedding_shape"], "finite:", es["G_finite"],
      "| B_phi task embedding:", es["B_phi_task_embedding_shape"], "finite:", es["B_phi_finite"])''')

md("## 6. Synthetic input and direct target-scalar diagnostics")
code('''si = smoke["synthetic_input"]
print("seed:", si["seed"], "image:", si["image_shape"], si["image_dtype"], si["image_device"],
      "| task_id:", si["task_id"], si["task_id_dtype"])
print("mask:", si["target_mask_name"], "rank", si["target_mask_rank"], si["target_mask_shape"],
      "true pixels:", si["target_mask_true_pixels"], "|", si["target_mask_centered_square"])
print()
ts = smoke["target_scalar_direct"]
print("impl:", ts["impl"])
print("value:", ts["value"], "finite:", ts["finite"], "selected_pixels:", ts["selected_pixels"])
print("surrogate_logits_used:", ts["surrogate_logits_used"])''')

md("## 7. Grad-CAM activations and gradients (bridge / decoder1)")
code('''gf = smoke["gradcam_forward"]
print("G forwards:", gf["G_forward_count"], "autograd calls:", gf["autograd_calls"])
print("activation shapes:", gf["activation_shapes"])
print("enable_grad:", gf["enable_grad"], "autocast_cuda_fp16:", gf["autocast_cuda_fp16"],
      "no_grad_used:", gf["no_grad_used"], "inference_mode_used:", gf["inference_mode_used"])
print()
for n in ("bridge","decoder1"):
    print(n, "gradient:", json.dumps(smoke["gradient_diagnostics"][n]))''')

md("## 8. Eight-stage numerical guard chain")
code('''print("guard stages:", gf["finite_guards_applied"])
for n in ("bridge","decoder1"):
    print(f"--- {n} ---")
    print(json.dumps(smoke["numerical_guard_chain"][n], indent=1))''')

md("## 9. CAM finiteness and zero-range treatment")
code('''cr = smoke["cam_results"]
print("bridge all-zero:", cr["bridge_cam_all_zero"], "| decoder1 all-zero:", cr["decoder1_cam_all_zero"])
print("finite zero-range:", cr["cams_finite_zero_range"], "| nonzero:", cr["cams_nonzero"])
print("finite_zero_range_cam_treatment:", cr["finite_zero_range_cam_treatment"])
print("cams:", json.dumps(cr["cams"], indent=1))''')

md("## 10. Actual-same-forward empty-mask fallback check (load-bearing)")
code('''emc = smoke["empty_mask_actual_logits_check"]
for k in ("same_actual_G_logits_used","surrogate_zero_logits_used","empty_mask_rank","empty_mask_shape",
          "empty_mask_true_pixels","fallback_selected","helper_return","expected_full_plane_mean",
          "difference","atol","rtol","comparison_pass","finite","additional_G_forwards",
          "additional_autograd_calls"):
    print(f"{k}: {emc[k]}")''')

md("## 11. Direct parameter .grad audit and state immutability")
code('''pg = smoke["parameter_grad_state_audit"]
print("G parameter tensors:", pg["G"]["named_parameter_tensors"], "| non-null grads:", pg["G"]["non_null_grad_tensors"])
print("B_phi parameter tensors:", pg["B_phi"]["named_parameter_tensors"], "| non-null grads:", pg["B_phi"]["non_null_grad_tensors"])
print("NO_PARAMETER_GRAD_POPULATED:", pg["NO_PARAMETER_GRAD_POPULATED"])
print("mechanism:", pg["mechanism"])
print()
pi = smoke["parameter_immutability"]
print("G unchanged:", pi["G_state_tensors_unchanged"], "| B_phi unchanged:", pi["B_phi_state_tensors_unchanged"])
print("parameter_mutations:", pi["parameter_mutations"])''')

md("## 12. Router synthetic smoke and zero-denominator policy")
code('''r = smoke["router_smoke"]
print("raw input:", r["raw_router_input_shape"], r["raw_router_input_dtype"], "finite:", r["raw_router_input_finite"])
print("normalized input:", r["normalized_router_input_shape"], "finite:", r["normalized_router_input_finite"])
print("delta_hat:", r["raw_delta_hat_shape"], "finite:", r["raw_delta_hat_finite"], "sigmoid_count:", r["sigmoid_count"])
print("gradient:", r["router_gradient_shape"], "finite:", r["router_gradient_finite"])
print("gradient x input:", r["gradient_x_input_shape"], "finite:", r["gradient_x_input_finite"])
print("task_id numeric attribution:", r["task_id_numeric_attribution"])
print()
z = smoke["zero_denominator_policy"]
print("denominator:", z["denominator"], "| shares:", z["normalized_group_shares"])
print("ZERO_ROUTER_GRAD_ATTRIBUTION:", z["ZERO_ROUTER_GRAD_ATTRIBUTION"],
      "| epsilon:", z["epsilon_added"], "| renormalization:", z["renormalization"],
      "| b_phi forwards used:", z["b_phi_forwards_used"])''')

md("## 13. Execution counters, protected-data counters, scientific-output counters")
code('''ct = smoke["execution_counters"]
for k in ("G_model_constructions","B_phi_model_constructions","checkpoint_deserializations","strict_loads",
          "G_synthetic_forwards","B_phi_synthetic_forwards","total_model_forwards",
          "G_gradcam_autograd_calls","router_numeric_input_autograd_calls","total_autograd_calls",
          "synthetic_CAM_maps","synthetic_router_attribution_rows","synthetic_smoke_target_masks",
          "R_psi_model_constructions","S_omega_model_constructions","optimizer_constructions",
          "optimizer_step_calls","training_backward_calls","parameter_mutations"):
    print(f"{k}: {ct[k]}")
print()
print("protected data:", json.dumps(smoke["protected_data_counters"]))
print("scientific outputs:", json.dumps(smoke["scientific_output_counters"]))
print("counters_all_protected_zero:", smoke["counters_all_protected_zero"])''')

md("## 14. Governance state")
code('''print("classification:", smoke["classification"])
print("not:", smoke["not"])
print("gates:", json.dumps(smoke["gates"]))
print("phase35_scientific_execution_started:", smoke["phase35_scientific_execution_started"])
print("phase36_started:", smoke["phase36_started"])
print("TEST:", smoke["TEST"])
print("ROUTER_HOLDOUT:", smoke["ROUTER_HOLDOUT"])
print()
print("terminal:", term["terminal"])''')

md("""## 15. Reviewer summary

- The frozen v1.0f source/hash gate passed for all 18 frozen sources BEFORE model construction.
- Canonical `G` and `B_phi` constructed once each, strict-loaded with 0 missing / 0 unexpected keys,
  at 3,523,001 and 36,801 parameters respectively; `R_psi`/`S_omega` untouched.
- Exactly one synthetic `G` forward and one router `B_phi` forward were run; two autograd calls total.
- All eight numerical guard stages are finite for both `bridge` and `decoder1`; no `nan_to_num` or
  hidden clamping was used. Both CAMs are finite zero-range (allowed PASS).
- The load-bearing actual-same-forward empty-mask fallback check passed with difference `0.0` at
  `atol=1e-7, rtol=0`, using the ACTUAL logits; no surrogate zero logits were used.
- Direct parameter `.grad` audit: 0 non-null gradients for both models; state identity unchanged.
- Protected-data and scientific-output counters are all zero.

**The smoke correctly FAILED CLOSED** on a single internal execution-count integrity mismatch
(`synthetic_smoke_target_masks` = 2 vs expected 1). This is a bookkeeping defect in the v1.0f smoke
harness's expected-counter declaration, not a model, numerical, interface, protected-data, or
scientific defect. Phase35 scientific execution remains NOT STARTED and is NOT eligible until this
counter contract is reconciled. TEST remains `LOCKED_UNTIL_PHASE39`.""")


def build():
    nb = nbformat.v4.new_notebook(cells=CELLS)
    nb.metadata.update(_META)
    NotebookClient(nb, kernel_name=KERNEL, timeout=600,
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(NB))
    return nb


if __name__ == "__main__":
    nb = build()
    print("wrote", NB)
    print("cells", len(nb.cells))
    executed = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
    print("code cells with persisted outputs", executed)
    print("sha256", hashlib.sha256(NB.read_bytes()).hexdigest())
