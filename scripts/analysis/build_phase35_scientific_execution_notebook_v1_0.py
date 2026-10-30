#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build + execute the Phase 35 v1.0 SCIENTIFIC EXECUTION reviewer notebook (READ-ONLY).

The notebook loads ONLY the produced v1.0 scientific / governance artifacts:
  reports/audits/phase35_first_scientific_execution_v1_0.json
  reports/audits/phase35_first_scientific_execution_final_check_v1_0.json
  reports/audits/phase35_first_scientific_execution_terminal_v1_0.json
  reports/audits/phase35_scientific_execution_static_preflight_v1_0.json
  reports/audits/phase35_scientific_execution_source_freeze_v1_0.json
  reports/audits/phase35_interpretability_scientific_result_v1_0.json
and prints their contents.

It performs NO model construction, NO checkpoint deserialization, NO forward, NO autograd,
NO Grad-CAM, NO router attribution, NO training, and touches no protected data.
Import surface: hashlib, json, pathlib ONLY.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NB = ROOT / "notebooks" / "phasewise" / "phase_35_interpretability"
OUT = NB / "phase35_interpretability_scientific_execution_v1_0_review.ipynb"


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(*lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": list(lines)}


def build():
    cells = [
        md(
            "# Phase 35 v1.0 - FIRST SCIENTIFIC EXECUTION\n",
            "## Feature Attribution & Visual Interpretability\n",
            "\n",
            "### Reviewer Notebook (read-only)\n",
            "\n",
            "**Classification:** `READ_ONLY_PHASE35_V1_0_SCIENTIFIC_EXECUTION_REVIEWER_NOTEBOOK`\n",
            "**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0`\n",
            "**Claim type:** `DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE`\n",
            "\n",
            "**Purpose:** confirm that the single authorized Phase35 scientific execution produced the four\n",
            "evidence families I1-I4, figures F1-F7, the frozen arrays/tables and the scientific result\n",
            "artifact - subject to the frozen data-access, counter and claim boundaries.\n",
            "\n",
            "This notebook **reads** artifacts only. It performs no model construction, no checkpoint\n",
            "deserialization, no forward, no autograd, no Grad-CAM, no router attribution, no training, and\n",
            "touches no protected data (no raw VAL images, no VAL GT, no `ROUTER_HOLDOUT`, no `TEST`).\n",
            "Import surface is limited to `hashlib`, `json`, `pathlib`.\n",
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
            "ex   = jload(AUD / \"phase35_first_scientific_execution_v1_0.json\")\n",
            "fc   = jload(AUD / \"phase35_first_scientific_execution_final_check_v1_0.json\")\n",
            "term = jload(AUD / \"phase35_first_scientific_execution_terminal_v1_0.json\")\n",
            "pre  = jload(AUD / \"phase35_scientific_execution_static_preflight_v1_0.json\")\n",
            "frz  = jload(AUD / \"phase35_scientific_execution_source_freeze_v1_0.json\")\n",
            "res  = jload(AUD / \"phase35_interpretability_scientific_result_v1_0.json\")\n",
            "\n",
            "print(\"Phase35 v1.0 first scientific execution review (READ-ONLY)\")\n",
            "print(\"No model construction, no checkpoint deserialization, no forward, no autograd, no\")\n",
            "print(\"Grad-CAM, no router attribution, no images, no VAL GT, no HOLDOUT/TEST, no training.\")\n",
        ),
        md("## 1. Pre-execution gates (static preflight + source freeze)\n"),
        code(
            "print(\"static preflight all_pass:\", pre[\"all_pass\"],\n",
            "      f'({pre[\"passed\"]}/{pre[\"total_checks\"]})')\n",
            "print(\"preflight torch_imported:\", pre[\"torch_imported\"])\n",
            "print(\"source freeze all_pass:\", frz[\"all_pass\"])\n",
            "print(\"driver frozen before first protected read:\",\n",
            "      frz[\"scientific_driver_frozen_before_first_protected_read\"])\n",
            "print(\"frozen source count:\", len(frz[\"frozen_sources\"]))\n",
            "print(\"authority SHA mismatch:\", frz[\"authority_sha_mismatch\"])\n",
            "print(\"source_freeze_utc:\", frz[\"source_freeze_utc\"])\n",
        ),
        md("## 2. Execution discipline (single invocation, freeze precedes first read)\n"),
        code(
            "print(\"gate_env:\", ex[\"gate_env\"])\n",
            "print(\"supervisor_authorization:\", ex[\"supervisor_authorization\"])\n",
            "print(\"single_authorized_invocation:\", ex[\"single_authorized_invocation\"])\n",
            "print(\"retry_performed:\", ex[\"retry_performed\"])\n",
            "print(\"post_open_patch_performed:\", ex[\"post_open_patch_performed\"])\n",
            "print(\"first_attempt_preserved:\", ex[\"first_attempt_preserved\"])\n",
            "print(\"source_freeze_utc:\", ex[\"source_freeze_utc\"])\n",
            "print(\"first_scientific_read_utc:\", ex[\"first_scientific_read_utc\"])\n",
            "print(\"freeze precedes first read:\", ex[\"freeze_precedes_first_read\"])\n",
            "print(\"authority gates all matched:\", ex[\"authority_gates_all_match\"])\n",
        ),
        md("## 3. Four evidence families (never merged)\n"),
        code(
            "print(\"families:\", json.dumps(ex[\"evidence_families\"], indent=1))\n",
            "print(\"families_never_merged:\", ex[\"families_never_merged\"])\n",
            "print(\"claim_type:\", ex[\"claim_type\"])\n",
        ),
        md("## 4. Execution integrity counters\n"),
        code(
            "print(json.dumps(ex[\"execution_integrity\"], indent=1))\n",
        ),
        md("## 5. Protected-data and training exclusions\n"),
        code(
            "ei = ex[\"execution_integrity\"]\n",
            "print(\"VAL GT reads:\", ei[\"val_gt_reads\"])\n",
            "print(\"ROUTER_HOLDOUT reads:\", ei[\"router_holdout_reads\"])\n",
            "print(\"TEST reads:\", ei[\"test_reads\"])\n",
            "print(\"TRAIN raw reads:\", ei[\"train_raw_reads\"])\n",
            "print(\"raw VAL image reads:\", ei[\"raw_val_image_reads\"],\n",
            "      \"(authorized max\", ei[\"max_authorized_raw_val_image_reads\"], \")\")\n",
            "print(\"R_psi constructions:\", ei[\"R_psi_constructions\"])\n",
            "print(\"S_omega constructions:\", ei[\"S_omega_constructions\"])\n",
            "print(\"optimizer constructions/step:\", ei[\"optimizer_constructions\"],\n",
            "      \"/\", ei[\"optimizer_step_calls\"])\n",
            "print(\"training backward calls:\", ei[\"training_backward_calls\"])\n",
            "print(\"parameter mutations:\", ei[\"parameter_mutations\"])\n",
            "print(\"model parameters unchanged:\", ex[\"model_parameters_unchanged\"])\n",
            "print(\"no parameter .grad populated:\",\n",
            "      ex[\"parameter_grad_state_audit\"][\"NO_PARAMETER_GRAD_POPULATED\"])\n",
        ),
        md("## 6. Figures F1-F7 and F8 ineligibility\n"),
        code(
            "print(\"figures:\", json.dumps(ex[\"figures_produced\"], indent=1))\n",
            "print(\"figure_count:\", ex[\"figure_count\"])\n",
            "print(\"F8_regional_implemented:\", ex[\"F8_regional_implemented\"])\n",
            "print(\"outcome_selected_panels_used:\", ex[\"outcome_selected_panels_used\"])\n",
            "print(\"display subset resolved before saliency:\",\n",
            "      ex[\"display_subset_resolved_before_saliency\"])\n",
            "print(\"thresholds:\", json.dumps(ex[\"thresholds\"]))\n",
        ),
        md("## 7. Arrays and tables\n"),
        code(
            "print(\"arrays:\", json.dumps(ex[\"arrays_produced\"], indent=1))\n",
            "print(\"tables:\", json.dumps(ex[\"tables_produced\"], indent=1))\n",
        ),
        md("## 8. Scientific result artifact\n"),
        code(
            "print(\"scientific result path:\", ex[\"scientific_result_artifact\"])\n",
            "print(\"scientific result sha256:\", ex[\"scientific_result_sha256\"])\n",
            "print(\"result claim_type:\", res[\"claim_type\"])\n",
            "print(\"result families:\", json.dumps(res[\"evidence_families\"], indent=1))\n",
        ),
        md("## 9. Final check and terminal\n"),
        code(
            "print(\"final check all_pass:\", fc[\"all_pass\"],\n",
            "      f'({fc[\"passed\"]}/{fc[\"total_checks\"]})')\n",
            "for c in fc[\"checks\"]:\n",
            "    if not c[\"pass\"]:\n",
            "        print(\"  FAIL\", c[\"id\"], c[\"desc\"])\n",
            "print(\"terminal_state:\", term[\"terminal_state\"])\n",
            "print(\"phase35 scientific execution started:\",\n",
            "      term[\"phase35_scientific_execution_started\"])\n",
            "print(\"phase35 scientific execution invocations:\",\n",
            "      term[\"phase35_scientific_execution_invocations\"])\n",
            "print(\"phase36 started:\", term[\"phase36_started\"])\n",
            "print(\"test state:\", term[\"test_state\"])\n",
            "print(\"terminal:\", term[\"terminal_string\"])\n",
        ),
        md("## 10. Reviewer conclusions (descriptive model-mechanism evidence only)\n"),
        code(
            "print(\"PASS: static preflight 31/31 before execution\", pre[\"all_pass\"])\n",
            "print(\"PASS: driver frozen before the first protected read\",\n",
            "      frz[\"scientific_driver_frozen_before_first_protected_read\"])\n",
            "print(\"PASS: freeze precedes first scientific read\", ex[\"freeze_precedes_first_read\"])\n",
            "print(\"PASS: four families I1-I4 executed and never merged\", ex[\"families_never_merged\"])\n",
            "print(\"PASS: F1-F7 produced; F8 not implemented\", ex[\"figure_count\"] == 7,\n",
            "      ex[\"F8_regional_implemented\"] is False)\n",
            "print(\"PASS: only 64 authorized VAL images read; zero GT\",\n",
            "      ex[\"execution_integrity\"][\"raw_val_image_reads\"] == 64,\n",
            "      ex[\"execution_integrity\"][\"val_gt_reads\"] == 0)\n",
            "print(\"PASS: VAL808 router attribution from the frozen GT-free cache\",\n",
            "      ex[\"execution_integrity\"][\"router_rows\"] == 808)\n",
            "print(\"PASS: no retry, no post-open patch, first attempt preserved\",\n",
            "      (not ex[\"retry_performed\"]) and (not ex[\"post_open_patch_performed\"]))\n",
            "print(\"PASS: no training, no optimizer, no parameter mutation\",\n",
            "      ex[\"execution_integrity\"][\"training_backward_calls\"] == 0,\n",
            "      ex[\"execution_integrity\"][\"parameter_mutations\"] == 0)\n",
            "print()\n",
            "print(\"Boundary: the evidence below is DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE. It is not a\")\n",
            "print(\"causal explanation, not feature necessity/sufficiency, not ground-truth localization\")\n",
            "print(\"accuracy, and not clinical or biological importance.\")\n",
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "jup-venv"},
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py", "mimetype": "text/x-python", "name": "python",
                "nbconvert_exporter": "python", "pygments_lexer": "ipython3",
                "version": "3.11.9",
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

    n_err = sum(1 for c in nbf.cells for o in c.get("outputs", [])
                if o.get("output_type") == "error")
    print("cell errors:", n_err)
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
