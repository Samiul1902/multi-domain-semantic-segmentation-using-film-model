"""Build + execute the Phase 35 v1.0h synthetic-smoke reviewer notebook (READ-ONLY).

The notebook loads ONLY the produced v1.0h artifacts and the v1.0h1 governance artifacts:
  reports/audits/phase35_synthetic_interpretability_smoke_v1_0h.json
  reports/audits/phase35_synthetic_smoke_provenance_v1_0h.json
  reports/audits/phase35_synthetic_smoke_final_check_v1_0h.json
  reports/audits/phase35_synthetic_smoke_terminal_v1_0h.json
  reports/audits/phase35_preexecution_source_freeze_v1_0h1.json
  reports/audits/phase35_synthetic_smoke_eligibility_v1_0h1.json
and prints their contents. It performs NO model construction, NO checkpoint deserialization,
NO forward, NO autograd, NO Grad-CAM, NO router attribution, NO training, and touches no protected data.
Import surface: hashlib, json, pathlib ONLY.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D://Softfors//jup")
NB = ROOT / "notebooks" / "phasewise" / "phase_35_interpretability"
OUT = NB / "phase35_interpretability_synthetic_smoke_v1_0h_review.ipynb"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(*lines: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": list(lines)}


def build() -> dict:
    cells = [
        md(
            "# Phase 35 v1.0h - Synthetic Interpretability Smoke\n",
            "## under the reconciled v1.0h1 source freeze\n",
            "\n",
            "### Reviewer Notebook (read-only)\n",
            "\n",
            "**Classification:** `READ_ONLY_PHASE35_V1_0H_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK`\n",
            "**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0h`\n",
            "**Smoke classification:** `PRE_SCIENTIFIC_SYNTHETIC_NUMERICAL_INTERFACE_AND_FULL_COUNTER_CONTRACT_VALIDATION`\n",
            "**Not:** `NOT_PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT`\n",
            "\n",
            "**Purpose:** confirm that the frozen v1.0h scientific / numerical / interface path remains valid\n",
            "and that the full **35-key** counter contract closes exactly under the reconciled v1.0h1 freeze.\n",
            "\n",
            "This notebook **reads** artifacts only. It performs no model construction, no checkpoint\n",
            "deserialization, no forward, no autograd, no Grad-CAM, no router attribution, no training, and\n",
            "touches no protected data (no raw VAL images, no real persisted `p_global`, no VAL GT, no VAL808\n",
            "router cache, no `ROUTER_HOLDOUT`, no `TEST`). Import surface is limited to `hashlib`, `json`,\n",
            "`pathlib`.\n",
        ),
        md("## 0. Setup (read-only artifact loading)\n"),
        code(
            "import hashlib\n",
            "import json\n",
            "from pathlib import Path\n",
            "\n",
            "ROOT = Path(r\"D://Softfors//jup\")\n",
            "AUD = ROOT / \"reports\" / \"audits\"\n",
            "\n",
            "def jload(p):\n",
            "    return json.loads(Path(p).read_text(encoding=\"utf-8\"))\n",
            "\n",
            "def sha(p):\n",
            "    return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n",
            "\n",
            "smoke = jload(AUD / \"phase35_synthetic_interpretability_smoke_v1_0h.json\")\n",
            "prov  = jload(AUD / \"phase35_synthetic_smoke_provenance_v1_0h.json\")\n",
            "fc    = jload(AUD / \"phase35_synthetic_smoke_final_check_v1_0h.json\")\n",
            "term  = jload(AUD / \"phase35_synthetic_smoke_terminal_v1_0h.json\")\n",
            "freeze = jload(AUD / \"phase35_preexecution_source_freeze_v1_0h1.json\")\n",
            "elig  = jload(AUD / \"phase35_synthetic_smoke_eligibility_v1_0h1.json\")\n",
            "\n",
            "print(\"Phase35 v1.0h synthetic smoke review (READ-ONLY)\")\n",
            "print(\"This notebook READS the produced v1.0h smoke/provenance/final-check/terminal artifacts\")\n",
            "print(\"plus the v1.0h1 reconciled freeze and eligibility governance JSONs only.\")\n",
            "print(\"No model construction, no checkpoint deserialization, no forward, no autograd, no Grad-CAM,\")\n",
            "print(\"no router attribution, no images, no real p_global, no VAL808 cache, no HOLDOUT/TEST, no training.\")\n",
        ),
        md("## 1. Result and terminal status\n"),
        code(
            "print(\"revision:\", smoke[\"revision\"])\n",
            "print(\"classification:\", smoke[\"classification\"])\n",
            "print(\"not:\", smoke[\"not\"])\n",
            "print(\"mode:\", smoke[\"mode\"])\n",
            "print(\"terminal_state:\", term[\"terminal_state\"])\n",
            "print(\"smoke_success:\", term[\"smoke_success\"])\n",
            "print(\"artifact_generation_pass:\", term[\"artifact_generation_pass\"])\n",
            "print(\"scientific_interface_checks_pass:\", term[\"scientific_interface_checks_pass\"])\n",
            "print(\"counter_contract_pass:\", term[\"counter_contract_pass\"])\n",
            "print(\"all_pass (== smoke_success):\", term[\"all_pass\"])\n",
            "print(\"terminal:\", term[\"terminal_string\"])\n",
        ),
        md("## 2. Reconciled authority binding (v1.0h1)\n"),
        code(
            "b = smoke[\"authority_binding\"]\n",
            "for k, v in b.items():\n",
            "    print(f\"{k}: sha256={v['sha256']}\" + (f\"  used_for_expected_table={v['used_for_expected_table']}\" if \"used_for_expected_table\" in v else \"\"))\n",
            "print()\n",
            "print(\"superseded v1.0h freeze preserved, NOT used for expected table:\",\n",
            "      b[\"superseded_freeze_v1_0h\"][\"used_for_expected_table\"] == False)\n",
            "print(\"execution source sha matches expected:\", prov[\"provenance\"][\"execution_source_sha_match\"])\n",
            "print(\"reconciled freeze sha:\", prov[\"provenance\"][\"reconciled_freeze_authority_sha256\"])\n",
        ),
        md("## 3. Eligibility and environment gates\n"),
        code(
            "e = elig[\"eligibility\"]\n",
            "print(\"synthetic_smoke_execution_eligible:\", e[\"synthetic_smoke_execution_eligible\"])\n",
            "print(\"synthetic_smoke_started (pre-run):\", e[\"synthetic_smoke_started\"])\n",
            "print(\"scientific_execution_eligible:\", e[\"scientific_execution_eligible\"])\n",
            "print(\"reconciled_freeze_expected_counter_count:\", e[\"reconciled_freeze_expected_counter_count\"])\n",
            "print()\n",
            "print(\"environment:\", json.dumps(prov[\"environment\"], indent=1))\n",
            "print()\n",
            "print(\"authority gates:\")\n",
            "for k, v in smoke[\"runtime_payload\"][\"authority_gates\"].items():\n",
            "    print(f\"  {k}: match={v['match']}\")\n",
        ),
        md("## 4. Pre-model counter baseline (fail-closed)\n"),
        code(
            "cb = smoke[\"runtime_payload\"][\"counter_baseline\"]\n",
            "print(\"legacy store is V0C store:\", cb[\"legacy\"][\"legacy_store_is_v0c_store\"])\n",
            "print(\"legacy counter count:\", cb[\"legacy\"][\"legacy_counter_count\"], \"| all zero:\", cb[\"legacy\"][\"all_legacy_counters_zero\"])\n",
            "print(\"extension counter count:\", cb[\"extension\"][\"extension_counter_count\"], \"| all zero:\", cb[\"extension\"][\"all_extension_counters_zero\"])\n",
            "print(\"extension keys:\", cb[\"extension\"][\"extension_counter_keys\"])\n",
        ),
        md("## 5. Canonical model construction, strict load, parameter counts\n"),
        code(
            "c = smoke[\"observed_counters\"]\n",
            "for k in (\"G_model_constructions\",\"B_phi_model_constructions\",\"checkpoint_deserializations\",\n",
            "          \"strict_loads\",\"R_psi_model_constructions\",\"R_psi_checkpoint_loads\",\"R_psi_forwards\",\n",
            "          \"S_omega_model_constructions\",\"S_omega_checkpoint_loads\",\"S_omega_forwards\"):\n",
            "    print(f\"{k}: {c[k]}\")\n",
            "print()\n",
            "print(\"G identity:\", json.dumps(prov[\"G_identity\"]))\n",
            "print(\"B_phi identity:\", json.dumps(prov[\"B_phi_identity\"]))\n",
            "print(\"checkpoint identity match:\",\n",
            "      prov[\"checkpoint_identity\"][\"G\"][\"match\"],\n",
            "      prov[\"checkpoint_identity\"][\"B_phi\"][\"match\"])\n",
        ),
        md("## 6. FiLM sites and task embeddings\n"),
        code(
            "fs = smoke[\"runtime_payload\"][\"film_smoke\"]\n",
            "print(\"film all_pass:\", fs[\"all_pass\"], \"| sites:\", len(fs[\"per_task_site\"]))\n",
            "site_ch = {}\n",
            "for key, v in fs[\"per_task_site\"].items():\n",
            "    dom, site = key.split(\"|\")\n",
            "    site_ch.setdefault(site, set()).add((v[\"gamma_len\"], v[\"expected_channels\"]))\n",
            "for site, vals in sorted(site_ch.items()):\n",
            "    print(f\"  {site}: {sorted(vals)}\")\n",
            "print(\"all finite:\", all(v[\"finite\"] for v in fs[\"per_task_site\"].values()))\n",
            "print(\"all channel-exact:\", all(v[\"channel_count_exact\"] for v in fs[\"per_task_site\"].values()))\n",
            "print()\n",
            "es = smoke[\"runtime_payload\"][\"embedding_smoke\"]\n",
            "print(\"G task embedding:\", es[\"G_task_embedding_shape\"], \"finite:\", es[\"G_finite\"])\n",
            "print(\"B_phi task embedding:\", es[\"B_phi_task_embedding_shape\"], \"finite:\", es[\"B_phi_finite\"])\n",
            "print(\"scientific_embedding_tables_emitted:\", es[\"scientific_embedding_tables_emitted\"])\n",
        ),
        md("## 7. Synthetic Grad-CAM: target scalar, gradients, CAMs\n"),
        code(
            "gs = smoke[\"runtime_payload\"][\"gradcam_smoke\"]\n",
            "print(\"target scalar:\", gs[\"target_scalar\"], \"finite:\", gs[\"target_scalar_finite\"])\n",
            "print(\"target_scalar_impl:\", gs[\"target_scalar_impl\"])\n",
            "print(\"normalization_impl:\", gs[\"normalization_impl\"])\n",
            "print(\"gradient_impl:\", gs[\"gradient_impl\"])\n",
            "print(\"activation shapes:\", gs[\"activation_shapes\"])\n",
            "print(\"scalar target evals:\", gs[\"scalar_target_evaluations\"], \"autograd calls:\", gs[\"autograd_calls\"])\n",
            "print(\"all gradients finite:\", gs[\"all_gradients_finite\"])\n",
            "print(\"grad shapes match activations:\", gs[\"gradient_shapes_match_activations\"])\n",
            "print(\"finite guards applied:\", len(gs[\"finite_guards_applied\"]), gs[\"finite_guards_applied\"])\n",
            "print(\"all prenorm CAMs finite:\", gs[\"all_prenorm_cams_finite\"])\n",
            "print(\"all normalized CAMs finite:\", gs[\"all_normalized_cams_finite\"])\n",
            "print(\"all cams all-zero:\", gs[\"all_cams_all_zero\"], \"| prenorm all-zero:\", gs[\"prenorm_all_zero\"])\n",
            "print(\"scientific_target_selection_used:\", gs[\"scientific_target_selection_used\"])\n",
            "print(\"rank4_workaround_used:\", gs[\"rank4_workaround_used\"])\n",
            "print(\"target mask rank/shape/name:\", gs[\"target_mask_rank\"], gs[\"target_mask_shape\"], gs[\"target_mask_name\"])\n",
        ),
        md("## 8. Per-layer gradient diagnostics (bridge, decoder1)\n"),
        code(
            "for n, g in gs[\"gradient_diagnostics\"].items():\n",
            "    print(f\"--- {n} ---\")\n",
            "    print(json.dumps(g, indent=1))\n",
        ),
        md("## 9. Actual-same-forward empty-mask observability (load-bearing)\n"),
        code(
            "em = gs[\"empty_mask_helper_check\"]\n",
            "for k in (\"same_actual_G_logits_used\",\"surrogate_zero_logits_used\",\"empty_mask_rank\",\n",
            "          \"empty_mask_shape\",\"empty_mask_true_pixels\",\"empty_mask_any\",\"fallback_selected\",\n",
            "          \"helper_return\",\"expected_full_plane_mean\",\"difference\",\"atol\",\"rtol\",\n",
            "          \"comparison_pass\",\"finite\",\"counter_category\",\"counts_as_primary_target_mask\",\n",
            "          \"additional_G_forwards\",\"additional_autograd_calls\"):\n",
            "    print(f\"{k}: {em[k]}\")\n",
        ),
        md("## 10. Direct parameter `.grad` audit and state immutability\n"),
        code(
            "pg = smoke[\"runtime_payload\"][\"parameter_grad_state_audit\"]\n",
            "print(\"G param tensors:\", pg[\"G\"][\"named_parameter_tensors\"], \"| non-null grads:\", pg[\"G\"][\"non_null_grad_tensors\"])\n",
            "print(\"B_phi param tensors:\", pg[\"B_phi\"][\"named_parameter_tensors\"], \"| non-null grads:\", pg[\"B_phi\"][\"non_null_grad_tensors\"])\n",
            "print(\"total non-null grads:\", pg[\"total_non_null_grad_tensors\"])\n",
            "print(\"NO_PARAMETER_GRAD_POPULATED:\", pg[\"NO_PARAMETER_GRAD_POPULATED\"])\n",
            "print()\n",
            "pi = smoke[\"runtime_payload\"][\"parameter_immutability\"]\n",
            "print(\"G identity before==after:\", pi[\"G_identity_before\"] == pi[\"G_identity_after\"])\n",
            "print(\"B_phi identity before==after:\", pi[\"B_phi_identity_before\"] == pi[\"B_phi_identity_after\"])\n",
            "print(\"MODEL_PARAMETERS_UNCHANGED:\", pi[\"MODEL_PARAMETERS_UNCHANGED\"])\n",
            "print(\"parameter_mutations:\", pi[\"parameter_mutations\"])\n",
        ),
        md("## 11. Router synthetic smoke and zero-denominator policy\n"),
        code(
            "rs = smoke[\"runtime_payload\"][\"router_smoke\"]\n",
            "print(\"raw input:\", rs[\"raw_router_input_shape\"], \"finite:\", rs[\"raw_router_input_finite\"])\n",
            "print(\"normalized input:\", rs[\"normalized_router_input_shape\"], \"finite:\", rs[\"normalized_router_input_finite\"])\n",
            "print(\"delta_hat:\", rs[\"raw_delta_hat_shape\"], \"finite:\", rs[\"raw_delta_hat_finite\"], \"sigmoid_count:\", rs[\"sigmoid_count\"])\n",
            "print(\"gradient:\", rs[\"router_gradient_shape\"], \"finite:\", rs[\"router_gradient_finite\"])\n",
            "print(\"gradient x input:\", rs[\"gradient_x_input_shape\"], \"finite:\", rs[\"gradient_x_input_finite\"])\n",
            "print(\"task_id dtype/requires_grad/numeric_attribution:\", rs[\"task_id_dtype\"], rs[\"task_id_requires_grad\"], rs[\"task_id_numeric_attribution\"])\n",
            "print()\n",
            "zd = smoke[\"runtime_payload\"][\"zero_denominator_policy\"]\n",
            "print(\"denominator:\", zd[\"denominator\"])\n",
            "print(\"normalized group shares:\", zd[\"normalized_group_shares\"])\n",
            "print(\"ZERO_ROUTER_GRAD_ATTRIBUTION:\", zd[\"ZERO_ROUTER_GRAD_ATTRIBUTION\"])\n",
            "print(\"epsilon_added:\", zd[\"epsilon_added\"], \"| renormalization:\", zd[\"renormalization\"])\n",
        ),
        md("## 12. Full 35-key counter table and ownership\n"),
        code(
            "print(\"observed key count:\", len(smoke[\"observed_counters\"]))\n",
            "print(\"expected key count:\", len(smoke[\"expected_counters\"]))\n",
            "print(\"counters == expected:\", smoke[\"observed_counters\"] == smoke[\"expected_counters\"])\n",
            "print(\"counters == canonical:\", smoke[\"observed_counters\"] == smoke[\"canonical_35_key_contract\"])\n",
            "print()\n",
            "print(\"--- observed counters (35) ---\")\n",
            "for k, v in smoke[\"observed_counters\"].items():\n",
            "    print(f\"{k}: {v}\")\n",
            "print()\n",
            "co = prov[\"counter_ownership\"]\n",
            "print(\"legacy owner module:\", co[\"legacy_counter_owner_module\"])\n",
            "print(\"legacy/extension/merged counts:\", co[\"legacy_key_count\"], co[\"extension_key_count\"], co[\"merged_key_count\"])\n",
            "print(\"ownership disjoint:\", co[\"ownership_disjoint\"])\n",
            "print(\"router writer store identity:\", co[\"router_writer_store_identity_verified\"])\n",
            "print(\"router reader store identity:\", co[\"router_reader_store_identity_verified\"])\n",
            "print(\"writer/reader bridge:\", co[\"router_counter_writer_reader_same_object_or_explicit_delta_bridge\"])\n",
        ),
        md("## 13. Contract structural checks and alias/primary/empty ownership\n"),
        code(
            "print(\"--- counter_contract_exact ---\")\n",
            "print(json.dumps(smoke[\"counter_contract_exact\"], indent=1))\n",
            "print()\n",
            "print(\"counter_keyset_exact:\", smoke[\"runtime_payload\"][\"counter_keyset_exact\"])\n",
            "print(\"counter_count_exact:\", smoke[\"runtime_payload\"][\"counter_count_exact\"])\n",
            "print(\"counter_values_exact:\", smoke[\"runtime_payload\"][\"counter_values_exact\"])\n",
            "print(\"counts_match_expected:\", smoke[\"runtime_payload\"][\"counts_match_expected\"])\n",
            "print()\n",
            "print(\"--- alias/primary/empty ownership ---\")\n",
            "print(json.dumps(smoke[\"runtime_payload\"][\"counter_contract\"], indent=1))\n",
        ),
        md("## 14. Protected-data and scientific-output counters\n"),
        code(
            "protected = [\"raw_VAL_image_reads\",\"real_persisted_VAL_probability_reads\",\"VAL_GT_reads\",\n",
            "             \"router_feature_cache_rows_read\",\"ROUTER_HOLDOUT_reads\",\"TEST_reads\",\"TRAIN_raw_reads\"]\n",
            "print(\"protected-data counters all zero:\", all(smoke[\"observed_counters\"][k] == 0 for k in protected))\n",
            "for k in protected:\n",
            "    print(f\"  {k}: {smoke['observed_counters'][k]}\")\n",
            "print()\n",
            "print(\"scientific_outputs:\", smoke[\"observed_counters\"][\"scientific_outputs\"])\n",
            "print(\"film scientific tables emitted:\", smoke[\"runtime_payload\"][\"film_smoke\"][\"scientific_film_tables_emitted\"])\n",
            "print(\"embedding scientific tables emitted:\", smoke[\"runtime_payload\"][\"embedding_smoke\"][\"scientific_embedding_tables_emitted\"])\n",
        ),
        md("## 15. Final check summary\n"),
        code(
            "print(\"final_check:\", fc[\"passed\"], \"/\", fc[\"total_checks\"], \"passed,\", fc[\"failed\"], \"failed\")\n",
            "print(\"all_pass:\", fc[\"all_pass\"])\n",
            "print(\"first_valid_v1_0h_smoke_attempt:\", fc[\"first_valid_v1_0h_smoke_attempt\"])\n",
            "print(\"smoke_retry_performed:\", fc[\"smoke_retry_performed\"])\n",
            "print()\n",
            "print(\"failed checks:\")\n",
            "for cid, ok in fc[\"checks\"].items():\n",
            "    if not ok:\n",
            "        print(f\"  {cid}\")\n",
            "print(\"  (none)\" if fc[\"failed\"] == 0 else \"\")\n",
            "print()\n",
            "print(\"terminal:\", term[\"terminal_string\"])\n",
        ),
        md("## 16. Governance state\n"),
        code(
            "print(\"classification:\", smoke[\"classification\"])\n",
            "print(\"smoke gate env:\", smoke[\"smoke_gate_env\"])\n",
            "print(\"science gate env NOT set:\", smoke[\"science_gate_env_not_set\"])\n",
            "print(\"invocation_count:\", prov[\"provenance\"][\"invocation_count\"])\n",
            "print(\"retry_performed:\", prov[\"provenance\"][\"retry_performed\"])\n",
            "print(\"terminal_state:\", term[\"terminal_state\"])\n",
            "print(\"first_phase35_scientific_execution_eligible_for_supervisor_review:\",\n",
            "      term[\"first_phase35_scientific_execution_eligible_for_supervisor_review\"])\n",
            "print(\"phase35_scientific_execution_started:\", term[\"phase35_scientific_execution_started\"])\n",
            "print(\"phase36_started:\", term[\"phase36_started\"])\n",
            "print(\"test_state:\", term[\"test_state\"])\n",
        ),
        md(
            "## 17. Reviewer summary\n",
            "\n",
            "- The reconciled v1.0h1 freeze authority and the exact v1.0h execution-source bytes were bound\n",
            "  and hash-verified BEFORE model construction; the superseded v1.0h freeze was preserved but its\n",
            "  stale nested counter table was NOT used.\n",
            "- Canonical `G` and `B_phi` were constructed once each and strict-loaded with 0 missing / 0\n",
            "  unexpected keys at 3,523,001 and 36,801 parameters; `R_psi` and `S_omega` were untouched.\n",
            "- All 20 FiLM task x site combinations were finite and channel-exact; task embeddings were finite\n",
            "  and correctly shaped; no scientific FiLM/embedding tables were emitted.\n",
            "- The single synthetic gradient-enabled G forward produced a finite rank-safe target scalar, finite\n",
            "  gradients matching activation shapes, all 8 finite guards, and finite prenorm / normalized CAMs\n",
            "  (finite zero-range fallback path; a nonzero synthetic CAM is not required).\n",
            "- The empty-mask observability check used the ACTUAL same-forward logits (no surrogate zero plane),\n",
            "  performed no extra forward / autograd, and its comparison passed at `atol=1e-7`, `rtol=0`.\n",
            "- The router synthetic path produced a finite `[4,202]` gradient and Gradient x Input, `[4]`\n",
            "  delta_hat, zero sigmoid applications, and a NULL-share zero-denominator policy with no epsilon\n",
            "  and no renormalization.\n",
            "- **The full 35-key counter contract closed exactly:** 35/35 keys, exact keyset, exact count, exact\n",
            "  values, `counts_match_expected = true`; `primary_synthetic_target_masks = 1`,\n",
            "  `synthetic_smoke_target_masks = 1`, `actual_logits_empty_mask_helper_checks = 1`, alias == primary,\n",
            "  and the empty mask was NOT counted as a primary target mask.\n",
            "- The router counter writer/reader store identity was verified; no post-hoc router-count injection.\n",
            "- No protected data was touched, no scientific output was emitted, no training occurred, and\n",
            "  Phase 36 was not started. The first valid v1.0h attempt was preserved with no retry.\n",
            "- Supervisor action: the first Phase35 scientific execution is now **eligible for supervisor\n",
            "  review** but NOT started. `PHASE35_EXECUTE` remains unset and `TEST` remains LOCKED_UNTIL_PHASE39.\n",
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "jup-venv"},
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py", "mimetype": "text/x-python", "name": "python",
                "nbconvert_exporter": "python", "pygments_lexer": "ipython3", "version": "3.11.9",
            },
        },
        "nbformat": 4, "nbformat_minor": 5,
    }


def main() -> int:
    nb = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("WROTE", OUT)

    import nbformat
    from nbclient import NotebookClient

    nbf = nbformat.read(str(OUT), as_version=4)
    client = NotebookClient(nbf, kernel_name="jup-venv", timeout=600, allow_errors=False)
    client.execute()
    nbformat.write(nbf, str(OUT))
    print("EXECUTED", OUT)

    n_err = 0
    for c in nbf.cells:
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                n_err += 1
    print("cell errors:", n_err)
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
