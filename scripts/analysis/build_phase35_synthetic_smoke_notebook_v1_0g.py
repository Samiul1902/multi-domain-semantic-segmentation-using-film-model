"""Build + execute the Phase 35 v1.0g synthetic-smoke reviewer notebook (READ-ONLY).

The notebook loads ONLY the produced v1.0g artifacts
  reports/audits/phase35_synthetic_interpretability_smoke_v1_0g.json
  reports/audits/phase35_synthetic_smoke_provenance_v1_0g.json
  reports/audits/phase35_synthetic_smoke_final_check_v1_0g.json
  reports/audits/phase35_synthetic_smoke_terminal_v1_0g.json
  reports/audits/phase35_v1_0g_transitive_authority_binding.json
and prints their contents. It performs NO model construction, NO checkpoint deserialization,
NO forward, NO autograd, NO Grad-CAM, NO router attribution, NO image access.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D://Softfors//jup")
NB = ROOT / "notebooks" / "phasewise" / "phase_35_interpretability"
OUT = NB / "phase35_interpretability_synthetic_smoke_v1_0g_review.ipynb"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(*lines: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": list(lines),
    }


def build() -> dict:
    cells = [
        md(
            "# Phase 35 v1.0g - Final Pre-Scientific Synthetic Interpretability Smoke\n",
            "\n",
            "## Reviewer Notebook (read-only)\n",
            "\n",
            "**Classification:** `READ_ONLY_PHASE35_V1_0G_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK`\n",
            "**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0g`\n",
            "**Smoke classification:** `PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION`\n",
            "**Purpose:** confirm that the v1.0f scientific / numerical / interface path remains valid and\n",
            "that the v1.0g counter-contract repair closes exactly.\n",
            "\n",
            "This notebook **reads** artifacts only. It performs no model construction, no checkpoint\n",
            "deserialization, no forward, no autograd, no Grad-CAM, no router attribution, and touches no\n",
            "protected data (no raw VAL images, no real persisted `p_global`, no VAL GT, no VAL808 router\n",
            "cache, no `ROUTER_HOLDOUT`, no `TEST`). Import surface is limited to `hashlib`, `json`,\n",
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
            "smoke = jload(AUD / \"phase35_synthetic_interpretability_smoke_v1_0g.json\")\n",
            "prov  = jload(AUD / \"phase35_synthetic_smoke_provenance_v1_0g.json\")\n",
            "fc    = jload(AUD / \"phase35_synthetic_smoke_final_check_v1_0g.json\")\n",
            "term  = jload(AUD / \"phase35_synthetic_smoke_terminal_v1_0g.json\")\n",
            "bind  = jload(AUD / \"phase35_v1_0g_transitive_authority_binding.json\")\n",
            "\n",
            "print(\"Phase35 v1.0g synthetic smoke review (READ-ONLY)\")\n",
            "print(\"This notebook READS the produced v1.0g smoke/provenance/final-check/terminal artifacts only.\")\n",
            "print(\"No model construction, no checkpoint deserialization, no forward, no autograd, no Grad-CAM,\")\n",
            "print(\"no router attribution, no images, no real p_global, no VAL808 cache, no HOLDOUT/TEST.\")\n",
        ),
        md("## 1. Result and terminal status\n"),
        code(
            "print(\"revision:\", smoke[\"revision\"])\n",
            "print(\"mode:\", smoke[\"mode\"])\n",
            "print(\"terminal_state:\", term[\"terminal_state\"])\n",
            "print(\"success:\", term[\"success\"])\n",
            "print(\"harness all_pass:\", smoke[\"all_pass\"])\n",
            "print(\"counter_contract_ok:\", smoke[\"counter_contract_ok\"])\n",
            "print(\"counts_match_expected:\", smoke[\"counts_match_expected\"])\n",
            "print(\"scientific_and_interface_checks:\", smoke[\"summary\"][\"scientific_and_interface_checks\"])\n",
            "print(\"is_phase35_scientific_execution:\", smoke[\"is_phase35_scientific_execution\"])\n",
            "print(\"not:\", smoke[\"not\"])\n",
            "print(\"first_valid_attempt_preserved:\", smoke[\"first_valid_attempt_preserved\"])\n",
            "print(\"retry_performed:\", smoke[\"retry_performed\"])\n",
        ),
        md(
            "## 2. Blocking root cause (bookkeeping, not scientific)\n",
            "\n",
            "Every model, numerical, interface, and protected-data check passed. The blocking condition is\n",
            "an **expected-counter-table / alias-mirror bookkeeping defect**:\n",
            "\n",
            "- `synthetic_smoke_target_masks` (alias) = 0 vs expected 1 - the alias was not mirrored from\n",
            "  the canonical primary counter (the v1.0g repair does not mirror into the v1.0c-local alias).\n",
            "- The expected table omits the router path rows (`B_phi_synthetic_forwards`,\n",
            "  `router_numeric_input_autograd_calls`, `total_autograd_calls`, `total_model_forwards`,\n",
            "  `synthetic_router_attribution_rows`), which the inherited v1.0c `smoke_router` helper does\n",
            "  increment.\n",
            "- The expected table key set is a strict subset (23 of 31) of the counter store; the 8\n",
            "  protected-data counters were never declared, and all observed 0.\n",
            "\n",
            "**Crucially, the v1.0g load-bearing repair itself is effective:**\n",
            "`primary_synthetic_target_masks` = 1, `actual_logits_empty_mask_helper_checks` = 1, and the\n",
            "empty mask was NOT counted as a primary target mask.\n",
        ),
        code(
            "print(\"blocking defect:\", term[\"blocking_defect\"][\"id\"])\n",
            "print(\"defect class:\", term[\"blocking_defect\"][\"class\"])\n",
            "print()\n",
            "print(\"--- observed vs expected counter mismatches ---\")\n",
            "for o in term[\"blocking_defect\"][\"observations\"]:\n",
            "    print(f\"  {o['counter']}: observed={o['observed']} expected={o['expected']} | {o['cause']}\")\n",
        ),
        md("## 3. Load-bearing counter contract (§L)\n"),
        code(
            "lc = smoke[\"load_bearing_counter_contract\"]\n",
            "for k in (\"contract\",\"primary_synthetic_target_masks\",\"synthetic_smoke_target_masks_alias\",\n",
            "          \"actual_logits_empty_mask_helper_checks\",\"additional_G_forwards_for_empty_mask\",\n",
            "          \"additional_autograd_calls_for_empty_mask\",\"alias_equals_primary\",\n",
            "          \"empty_mask_not_counted_as_primary\",\"counter_contract_ok\"):\n",
            "    print(f\"{k}: {lc[k]}\")\n",
            "print()\n",
            "print(\"repair effectiveness (primary + empty-mask categories):\")\n",
            "rc = term[\"blocking_defect\"][\"repaired_contract_verified\"]\n",
            "for k, v in rc.items():\n",
            "    print(f\"  {k}: {v}\")\n",
        ),
        md("## 4. Authority binding and environment\n"),
        code(
            "print(\"v1_0g_counter_authority_bound:\", bind[\"v1_0g_counter_authority_bound\"])\n",
            "print(\"v1_0f_scientific_authority_bound:\", bind[\"v1_0f_scientific_authority_bound\"])\n",
            "print(\"all_hashes_match:\", bind[\"all_hashes_match\"])\n",
            "print(\"scientific_semantics_changed:\", bind[\"scientific_semantics_changed\"])\n",
            "print(\"n_authorities:\", len(bind[\"authorities\"]))\n",
            "print(\"mismatches:\", bind[\"mismatches\"])\n",
            "print()\n",
            "print(\"environment:\", json.dumps(smoke[\"environment\"], indent=1))\n",
            "print()\n",
            "print(\"authority gates:\")\n",
            "for k, v in smoke[\"authority_gates\"].items():\n",
            "    print(f\"  {k}: match={v['match']}\")\n",
        ),
        md("## 5. Canonical model construction, strict load, parameter counts\n"),
        code(
            "c = smoke[\"counters\"]\n",
            "for k in (\"G_model_constructions\",\"B_phi_model_constructions\",\"checkpoint_deserializations\",\n",
            "          \"strict_loads\",\"R_psi_model_constructions\",\"R_psi_checkpoint_loads\",\"R_psi_forwards\",\n",
            "          \"S_omega_model_constructions\",\"S_omega_checkpoint_loads\",\"S_omega_forwards\"):\n",
            "    print(f\"{k}: {c[k]}\")\n",
            "print()\n",
            "print(\"G identity:\", json.dumps(smoke[\"G_identity\"]))\n",
            "print(\"B_phi identity:\", json.dumps(smoke[\"B_phi_identity\"]))\n",
            "print(\"checkpoint identity match:\",\n",
            "      smoke[\"checkpoint_identity\"][\"G\"][\"match\"],\n",
            "      smoke[\"checkpoint_identity\"][\"B_phi\"][\"match\"])\n",
        ),
        md("## 6. FiLM sites and task embeddings\n"),
        code(
            "fs = smoke[\"film_smoke\"]\n",
            "print(\"film all_pass:\", fs[\"all_pass\"], \"| sites:\", len(fs[\"per_task_site\"]))\n",
            "site_ch = {}\n",
            "for key, v in fs[\"per_task_site\"].items():\n",
            "    dom, site = key.split(\"|\")\n",
            "    site_ch.setdefault(site, set()).add((v[\"gamma_len\"], v[\"expected_channels\"]))\n",
            "for site, vals in site_ch.items():\n",
            "    print(f\"  {site}: {sorted(vals)}\")\n",
            "print(\"all finite:\", all(v[\"finite\"] for v in fs[\"per_task_site\"].values()))\n",
            "print(\"all channel-exact:\", all(v[\"channel_count_exact\"] for v in fs[\"per_task_site\"].values()))\n",
            "print()\n",
            "es = smoke[\"embedding_smoke\"]\n",
            "print(\"G task embedding:\", es[\"G_task_embedding_shape\"], \"finite:\", es[\"G_finite\"])\n",
            "print(\"B_phi task embedding:\", es[\"B_phi_task_embedding_shape\"], \"finite:\", es[\"B_phi_finite\"])\n",
            "print(\"scientific_embedding_tables_emitted:\", es[\"scientific_embedding_tables_emitted\"])\n",
        ),
        md("## 7. Synthetic Grad-CAM: target scalar, gradients, CAMs\n"),
        code(
            "gs = smoke[\"gradcam_smoke\"]\n",
            "print(\"target scalar:\", gs[\"target_scalar\"], \"finite:\", gs[\"target_scalar_finite\"])\n",
            "print(\"target_scalar_impl:\", gs[\"target_scalar_impl\"])\n",
            "print(\"normalization_impl:\", gs[\"normalization_impl\"])\n",
            "print(\"gradient_impl:\", gs[\"gradient_impl\"])\n",
            "print(\"activation shapes:\", gs[\"activation_shapes\"])\n",
            "print(\"scalar target evals:\", gs[\"scalar_target_evaluations\"], \"autograd calls:\", gs[\"autograd_calls\"])\n",
            "print(\"all gradients finite:\", gs[\"all_gradients_finite\"])\n",
            "print(\"grad shapes match activations:\", gs[\"gradient_shapes_match_activations\"])\n",
            "print(\"finite guards applied:\", gs[\"finite_guards_applied\"])\n",
            "print(\"all prenorm CAMs finite:\", gs[\"all_prenorm_cams_finite\"])\n",
            "print(\"all normalized CAMs finite:\", gs[\"all_normalized_cams_finite\"])\n",
            "print(\"prenorm all-zero:\", gs[\"prenorm_all_zero\"])\n",
            "print(\"scientific_target_selection_used:\", gs[\"scientific_target_selection_used\"])\n",
            "print(\"rank4_workaround_used:\", gs[\"rank4_workaround_used\"])\n",
        ),
        md("## 8. Per-layer gradient diagnostics\n"),
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
            "pg = smoke[\"parameter_grad_state_audit\"]\n",
            "print(\"G param tensors:\", pg[\"G\"][\"named_parameter_tensors\"], \"| non-null grads:\", pg[\"G\"][\"non_null_grad_tensors\"])\n",
            "print(\"B_phi param tensors:\", pg[\"B_phi\"][\"named_parameter_tensors\"], \"| non-null grads:\", pg[\"B_phi\"][\"non_null_grad_tensors\"])\n",
            "print(\"total non-null grads:\", pg[\"total_non_null_grad_tensors\"])\n",
            "print(\"NO_PARAMETER_GRAD_POPULATED:\", pg[\"NO_PARAMETER_GRAD_POPULATED\"])\n",
            "print()\n",
            "pi = smoke[\"parameter_immutability\"]\n",
            "print(\"G identity before==after:\", pi[\"G_identity_before\"] == pi[\"G_identity_after\"])\n",
            "print(\"B_phi identity before==after:\", pi[\"B_phi_identity_before\"] == pi[\"B_phi_identity_after\"])\n",
            "print(\"MODEL_PARAMETERS_UNCHANGED:\", pi[\"MODEL_PARAMETERS_UNCHANGED\"])\n",
        ),
        md("## 11. Router synthetic smoke and zero-denominator policy\n"),
        code(
            "rs = smoke[\"router_smoke\"]\n",
            "print(\"raw input:\", rs[\"raw_router_input_shape\"], \"finite:\", rs[\"raw_router_input_finite\"])\n",
            "print(\"normalized input:\", rs[\"normalized_router_input_shape\"], \"finite:\", rs[\"normalized_router_input_finite\"])\n",
            "print(\"delta_hat:\", rs[\"raw_delta_hat_shape\"], \"finite:\", rs[\"raw_delta_hat_finite\"], \"sigmoid:\", rs[\"sigmoid_applied\"])\n",
            "print(\"gradient:\", rs[\"router_gradient_shape\"], \"finite:\", rs[\"router_gradient_finite\"])\n",
            "print(\"gradient x input:\", rs[\"gradient_x_input_shape\"], \"finite:\", rs[\"gradient_x_input_finite\"])\n",
            "print(\"task_id requires_grad:\", rs[\"task_id_requires_grad\"], \"| numeric attribution:\", rs[\"task_id_numeric_attribution\"])\n",
            "print()\n",
            "zd = smoke[\"zero_denominator_policy\"]\n",
            "print(\"denominator:\", zd[\"denominator\"])\n",
            "print(\"normalized group shares:\", zd[\"normalized_group_shares\"])\n",
            "print(\"ZERO_ROUTER_GRAD_ATTRIBUTION:\", zd[\"ZERO_ROUTER_GRAD_ATTRIBUTION\"])\n",
            "print(\"epsilon_added:\", zd[\"epsilon_added\"], \"| renormalization:\", zd[\"renormalization\"])\n",
        ),
        md("## 12. Full counter table, protected-data, and scientific-output counters\n"),
        code(
            "print(\"--- counters (observed) ---\")\n",
            "for k, v in smoke[\"counters\"].items():\n",
            "    print(f\"{k}: {v}\")\n",
            "print()\n",
            "print(\"--- expected counters (declared) ---\")\n",
            "for k, v in smoke[\"expected_counters\"].items():\n",
            "    print(f\"{k}: {v}\")\n",
            "print()\n",
            "pc = smoke[\"protected_data_counters\"]\n",
            "print(\"protected data all zero:\", pc[\"all_zero\"])\n",
            "for k, v in pc.items():\n",
            "    if k != \"all_zero\":\n",
            "        print(f\"  {k}: {v}\")\n",
            "print(\"scientific_outputs:\", smoke[\"scientific_output_counters\"])\n",
        ),
        md("## 13. Final check summary\n"),
        code(
            "print(\"final_check:\", fc[\"passed\"], \"/\", fc[\"total_checks\"], \"passed,\", fc[\"failed\"], \"failed\")\n",
            "print(\"blocking defect:\", fc[\"blocking_defect\"])\n",
            "print(\"blocking defect scope:\", fc[\"blocking_defect_scope\"])\n",
            "print(\"scientific_and_interface_checks_passed:\", fc[\"scientific_and_interface_checks_passed\"])\n",
            "print()\n",
            "print(\"failed checks:\")\n",
            "for chk in fc[\"checks\"]:\n",
            "    if not chk[\"pass\"]:\n",
            "        print(f\"  {chk['id']}: {chk['detail']}\")\n",
            "print()\n",
            "print(\"terminal:\", term[\"terminal_string\"])\n",
            "print(\"supervisor_action_required:\", term[\"supervisor_action_required\"])\n",
            "print(\"recommended_next_revision:\", term[\"recommended_next_revision\"])\n",
        ),
        md("## 14. Governance state\n"),
        code(
            "print(\"classification:\", smoke[\"classification\"])\n",
            "print(\"gate env set:\", smoke[\"gate_env_set\"])\n",
            "print(\"science gate env set:\", smoke[\"science_gate_env_set\"])\n",
            "print(\"invocation_count:\", smoke[\"invocation_count\"])\n",
            "print(\"phase36_started:\", smoke[\"phase36_started\"])\n",
            "print(\"training_performed:\", smoke[\"training_performed\"])\n",
            "print(\"optimizer_steps:\", smoke[\"optimizer_steps\"])\n",
            "print(\"first_phase35_scientific_execution_eligible_for_supervisor_review:\",\n",
            "      term[\"first_phase35_scientific_execution_eligible_for_supervisor_review\"])\n",
        ),
        md(
            "## 15. Reviewer summary\n",
            "\n",
            "- The frozen v1.0g counter authority (7 artifacts) and the transitive v1.0f scientific\n",
            "  authority (8 authorities, including the v1.0f source freeze, both checkpoints, the G model\n",
            "  source, the B_phi authority, the registry, the scientific specification, and the canonical\n",
            "  gallery) all hash-matched BEFORE model construction.\n",
            "- Canonical `G` and `B_phi` were constructed once each and strict-loaded with 0 missing / 0\n",
            "  unexpected keys at 3,523,001 and 36,801 parameters; `R_psi` and `S_omega` were untouched.\n",
            "- All FiLM sites were finite and channel-exact; task embeddings were finite and correctly\n",
            "  shaped; no scientific embedding tables were emitted.\n",
            "- The single synthetic gradient-enabled G forward produced a finite rank-safe target scalar,\n",
            "  finite gradients matching activation shapes, all 8 finite guards, and finite prenorm /\n",
            "  normalized CAMs (zero-range fallback path).\n",
            "- The empty-mask observability check used the ACTUAL same-forward logits (no surrogate zero\n",
            "  plane), performed no extra forward / autograd, and its comparison passed at `atol=1e-7`,\n",
            "  `rtol=0`.\n",
            "- The router synthetic path and zero-denominator policy behaved as specified; no parameter\n",
            "  `.grad` was populated; model parameters were byte-unchanged.\n",
            "- **The v1.0g load-bearing counter repair closed correctly for the two categories it targets:**\n",
            "  `primary_synthetic_target_masks = 1` and `actual_logits_empty_mask_helper_checks = 1`, and the\n",
            "  empty mask was not counted as a primary target mask.\n",
            "- The smoke nevertheless returned **BLOCKED** because of a separate bookkeeping defect: the\n",
            "  expected-counter table is a partial legacy snapshot (23 of 31 keys) and the v1.0c-local\n",
            "  backwards-compatible alias `synthetic_smoke_target_masks` was not mirrored from the new\n",
            "  canonical primary counter.\n",
            "- No protected data was touched, no scientific output was emitted, and Phase 36 was not\n",
            "  started. The first valid attempt was preserved with no retry.\n",
            "- Supervisor action: repair the expected-counter table and alias mirror in a single-step\n",
            "  source/governance-only revision (`v1.0h`); NO scientific protocol change is required.\n",
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "jup-venv"},
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.9",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
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
