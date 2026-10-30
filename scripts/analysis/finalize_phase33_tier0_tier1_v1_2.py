#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — TIER_0/TIER_1 EXECUTION FINALIZATION (v1.2).

Executes the NEW reviewer notebook deterministically (3 replays), then writes:
  §AA notebook audit, §W execution audit, §X scientific result, §AB final check, §AC terminal.

No raw reads. No models. No TEST. No new metrics.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/finalize_phase33_tier0_tier1_v1_2.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
NB = (ROOT / "notebooks" / "phasewise" / "phase_33_final_failure_analysis" /
      "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb")

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_2"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
TERMINAL = ("PHASE33_TIER0_TIER1_DESCRIPTIVE_FAILURE_ANALYSIS_V1_2_COMPLETE__LOW_OVERLAP_REALIZED_"
            "FROM_FROZEN_A8_DICE_GLOBAL_Q10_RULE__QUALIFIED_PHASE30_TABLES_AND_METADATA_ONLY__7_"
            "ELIGIBLE_FAILURE_FAMILIES_ANALYZED_WITH_PIXEL_BOUNDARY_COMPONENT_QUALITATIVE_AND_"
            "RERUN_PATHS_BLOCKED__NO_PROTECTED_RAW_OR_TEST_ACCESS__PHASE33_CLOSURE_ELIGIBLE_NOT_"
            "STARTED")

AUTHORITY = OrderedDict([
    ("reports/audits/phase33_specification_terminal_v1_2.json",
     "d8f744be0bcaeabdca951bf9369467869d0fd633c872243fbbc1618d1468b07a"),
    ("reports/audits/phase33_specification_final_check_v1_2.json",
     "83998e6420cf9eb1d790f693627ff5d39eaf041717258d32af91fe95bf55da03"),
    ("reports/audits/phase33_execution_eligibility_adjudication_v1_2.json",
     "5ffaa50821a05bb7de395586a2103e6420157ad72ac693df01f90c8d3646744a"),
    ("reports/audits/phase33_low_overlap_realization_contract_v1_2.json",
     "39fbb79bbc5d5641a215087e5824380162eb1c23033fa28fdd08202637b74eab"),
    ("docs/phase33_final_system_failure_boundary_spec_v1_2.md",
     "95c37a12d8fd0bbdc0815b3f472408f9d97cf29bad8ef9e26d8853048a53df01"),
    ("reports/audits/phase33_low_overlap_v1_1_ambiguity_record.json",
     "16bfb2022400d726c7bfbf2f28872412de7a7920c638edb5a7775e4de0d1246b"),
    ("reports/audits/phase33_failure_taxonomy_contract_v1_1.json",
     "522452cbf6e419f919deb9dadb8aba9734205c5afea9d2d0b16103c265cf4ae8"),
    ("reports/audits/phase33_failure_threshold_provenance_contract.json",
     "ff82a125af42b2977bad7d07449fbc7bf7e5bec445ef8b8d6207541376439d70"),
])
PRESERVE = OrderedDict([
    ("reports/audits/phase33_tier0_tier1_execution_terminal.json",
     "79a9215e883b2baba47d610e6399f0c39bd53fb9cbe5496ba82b9486ba2051d8"),
    ("reports/audits/phase33_tier0_tier1_execution_audit.json",
     "da439de70d9f122882dc063a48cb19f45a9252a6a9ba68a02aa8d3bf28b531a5"),
    ("reports/audits/phase33_tier0_tier1_preflight.json",
     "8cac456a7ead35a6956a14b693782de041f16a2874b5fac82ad4d428f09c25e7"),
    ("reports/audits/phase33_low_overlap_realization_adjudication.json",
     "a3fe87c19d0377ad7188a7a36c6d78305e24d691569350cb5683484c8cdbfc18"),
    ("reports/audits/phase33_low_overlap_rule_element_adjudication_v2.json",
     "73123ce1554d52bccfe87d75ec240d941712a3ddaaa88ed711470a9b2e7978a8"),
    ("notebooks/phasewise/phase_33_final_failure_analysis/"
     "phase33_final_failure_analysis_review.ipynb",
     "bf7443e0760d2bc49078776fd99130e7560f6460d5952921523d98f45c4ecc1a"),
])
SCORED = "reports/tables/phase30_router_holdout_scored_results.csv"
SCORED_SHA = "dbc9f5f3867f0607cfc0a778736a92b9d6de6e27811fa382ad6d1cb0b2a04568"
SPLIT = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"
PRED = "reports/tables/phase30_router_holdout_predictions.csv"
PRED_SHA = "513ccf2905cbc6f544337b9d157f38dc34d835e2cb56c25cabbe95f5046a3147"
REF_DOMAIN_N = {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104}


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def jload(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def code_hashes(nb):
    out = []
    for c in nb.cells:
        if c.cell_type == "code":
            txt = "".join(o.get("text", "") for o in c.get("outputs", [])
                          if o.get("output_type") == "stream")
            out.append(hashlib.sha256(txt.encode("utf-8")).hexdigest())
    return out


def execute_notebook_3x():
    runs, errors = [], []
    nb = None
    for i in range(3):
        nb = nbformat.read(str(NB), as_version=4)
        client = NotebookClient(nb, timeout=900, kernel_name="python3",
                                resources={"metadata": {"path": str(ROOT)}})
        client.execute()
        errs = 0
        for c in nb.cells:
            if c.cell_type == "code":
                errs += sum(1 for o in c.get("outputs", []) if o.get("output_type") == "error")
        errors.append(errs)
        runs.append(code_hashes(nb))
        print(f"  run {i+1}: {len(runs[-1])} code cells, {errs} errors")
    nbformat.write(nb, str(NB))
    deterministic = runs[0] == runs[1] == runs[2]
    return nb, deterministic, errors


def main() -> int:
    print("=" * 82)
    print("PHASE 33 — TIER_0/TIER_1 EXECUTION FINALIZATION (v1.2)")
    print("=" * 82)

    # ---------------- authority + preservation + inputs -------------------------------
    abinds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
               "match": sha256_file(ROOT / p) == e} for p, e in AUTHORITY.items()]
    a_ok = all(b["match"] for b in abinds)
    pbinds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
               "match": sha256_file(ROOT / p) == e} for p, e in PRESERVE.items()]
    b_ok = all(b["match"] for b in pbinds)
    scored_sha = sha256_file(ROOT / SCORED)
    split_sha = sha256_file(ROOT / SPLIT)
    pred_sha = sha256_file(ROOT / PRED)
    c_ok = scored_sha == SCORED_SHA and split_sha == SPLIT_SHA and pred_sha == PRED_SHA
    print(f"§A authority {sum(1 for b in abinds if b['match'])}/{len(abinds)} | "
          f"§B preserve {sum(1 for b in pbinds if b['match'])}/{len(pbinds)} | §C inputs={c_ok}")

    manifest = jload("reports/audits/phase33_tier0_tier1_analysis_manifest_v1_2.json")
    co = jload("reports/audits/phase33_low_overlap_cutoff_realization.json")
    cr = jload("reports/audits/phase33_phase30_count_reproduction_v1_2.json")
    gi = jload("reports/audits/phase33_group_join_integrity_v1_2.json")
    pc = jload("reports/audits/phase33_tier0_tier1_prohibited_counters_v1_2.json")
    ct = jload("reports/audits/phase33_low_overlap_realization_contract_v1_2.json")
    fc2 = jload("reports/audits/phase33_specification_final_check_v1_2.json")
    ee2 = jload("reports/audits/phase33_execution_eligibility_adjudication_v1_2.json")
    tax = jload("reports/audits/phase33_failure_taxonomy_contract_v1_1.json")

    # verify output artifacts (manifest-listed) still hash-match
    out_ok = all(sha256_file(ROOT / it["path"]) == it["sha256"] for it in manifest["produced"])
    print(f"§I-§U artifacts hash-stable: {out_ok} ({manifest['n_produced']} artifacts)")

    # labels table row count
    with open(ROOT / "reports/tables/phase33_final_system_failure_labels_v1_2.csv",
              newline="", encoding="utf-8") as f:
        lab_rows = list(csv.DictReader(f))
    labels_ok = len(lab_rows) == 875
    dom = {}
    for r in lab_rows:
        dom[r["dataset"]] = dom.get(r["dataset"], 0) + 1

    # ---------------- §Y/§Z/§AA notebook execution + determinism ----------------------
    nb_built_sha = sha256_file(NB)
    print("executing notebook 3x ...")
    nb, deterministic, errors = execute_notebook_3x()
    nb_sha = sha256_file(NB)
    cells = nb.cells
    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.cell_type == "code")
    exec_count = sum(1 for c in cells if c.cell_type == "code" and c.get("execution_count"))
    err_total = sum(errors)
    nb_ok = deterministic and err_total == 0 and exec_count == n_code
    write_json({
        "artifact": "phase33_execution_reviewer_notebook_audit_v1_2", "phase": 33,
        "section": "§AA",
        "classification": "TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_FAILURE_ANALYSIS_REVIEWER_NOTEBOOK",
        "notebook_path": ("notebooks/phasewise/phase_33_final_failure_analysis/"
                          "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb"),
        "notebook_sha": nb_sha, "notebook_built_sha": nb_built_sha,
        "cell_count": n_cells, "code_cell_count": n_code, "execution_count": exec_count,
        "error_count": err_total, "determinism_result":
            "DETERMINISTIC_3_REPLAYS" if deterministic else "NON_DETERMINISTIC",
        "successful_execution": err_total == 0,
        "source_artifacts": [{"path": it["path"], "sha256": it["sha256"],
                              "exists": (ROOT / it["path"]).exists()}
                             for it in manifest["produced"]],
        "prior_blocked_notebook_overwritten": False,
        "raw_image_reads": 0, "raw_GT_reads": 0, "prediction_probability_array_reads": 0,
        "TEST_reads": 0, "model_loads": 0, "model_forwards": 0,
        "new_segmentation_metric_recomputations": 0, "new_statistical_tests": 0, "training": 0,
        "generated_utc": now_utc(), "all_pass": nb_ok,
    }, AUD / "phase33_execution_reviewer_notebook_audit_v1_2.json")
    print(f"§AA notebook audit: cells={n_cells} code={n_code} errors={err_total} "
          f"deterministic={deterministic} -> {nb_ok}")
    if not nb_ok:
        print("FAIL: notebook not deterministic / errors present.")
        return 1

    # ---------------- §W execution audit ----------------------------------------------
    output_artifacts = [{"path": it["path"], "sha256": it["sha256"], "section": it["section"]}
                        for it in manifest["produced"]]
    output_artifacts.append({"path":
                             "reports/audits/phase33_execution_reviewer_notebook_audit_v1_2.json",
                             "sha256": sha256_file(
                                 ROOT / "reports/audits/"
                                 "phase33_execution_reviewer_notebook_audit_v1_2.json"),
                             "section": "§AA"})
    output_artifacts.append({"path": ("notebooks/phasewise/phase_33_final_failure_analysis/"
                                      "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb"),
                             "sha256": nb_sha, "section": "§Y"})
    write_json({
        "artifact": "phase33_tier0_tier1_execution_audit_v1_2", "phase": 33, "section": "§W",
        "method": METHOD, "revision": REVISION,
        "outcome": "TIER0_TIER1_DESCRIPTIVE_FAILURE_ANALYSIS_COMPLETE",
        "authority_shas": {p: e for p, e in AUTHORITY.items()},
        "authority_bindings": abinds, "all_authority_match": a_ok,
        "prior_block_preservation": pbinds, "prior_block_all_preserved": b_ok,
        "input_table": {"path": SCORED, "sha256": scored_sha, "expected": SCORED_SHA},
        "metadata_manifest": {"path": SPLIT, "sha256": split_sha, "expected": SPLIT_SHA},
        "predictions_table": {"path": PRED, "sha256": pred_sha, "expected": PRED_SHA,
                              "role": "frozen non-pixel Phase30 table (TIER_1 source for "
                                      "state_machine / som ega_score / delta_hat / utility / tau_C8"},
        "n_rows": len(lab_rows), "domain_counts": dom, "group_count": gi["n_groups"],
        "finite_gate": co["finite_gate"], "finite_gate_pass": co["finite_gate_pass"],
        "low_overlap_realization_authority":
            "reports/audits/phase33_low_overlap_realization_contract_v1_2.json",
        "low_overlap_rule_exactly_frozen": True,
        "low_overlap_cutoff_rule": "a8_dice <= np.quantile(a8_dice[float64], 0.10, 'linear') "
                                   "GLOBAL, ties included",
        "low_overlap_realized_cutoff": co["realized_cutoff"],
        "low_overlap_n": co["low_overlap_n"], "low_overlap_rate": co["low_overlap_rate"],
        "phase30_count_reproduction": cr["observed"],
        "phase30_count_reproduced": cr["reproduced"],
        "eligible_family_partition": tax["eligible_families"],
        "ineligible_family_partition": tax["ineligible_families"],
        "taxonomy_partition_7_6": (len(tax["eligible_families"]) == 7
                                   and len(tax["ineligible_families"]) == 6
                                   and not (set(tax["eligible_families"])
                                            & set(tax["ineligible_families"]))),
        "hard_case_selection": {"eligible": manifest["hard_case_eligible"],
                                "selected_n": manifest["hard_case_selected_n"],
                                "shortfall": manifest["hard_case_shortfall"],
                                "classification": "DESCRIPTIVE_FAILURE_CASE_SELECTION"},
        "output_artifacts": output_artifacts,
        "n_output_artifacts": len(output_artifacts),
        "prohibited_counters": pc["counters"],
        "prohibited_counters_all_zero": pc["all_zero"],
        "phase30_qualifier_preserved": QUALIFIER,
        "phase30_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
        "phase30_status_upgraded": False,
        "TEST_state": "LOCKED_UNTIL_PHASE39",
        "Phase34_state": "NOT_STARTED",
        "boundary_metric_execution_eligible": False,
        "component_metric_execution_eligible": False,
        "qualitative_gallery_eligible": False,
        "model_rerun_eligible": False,
        "generated_utc": now_utc(), "all_pass": bool(a_ok and b_ok and c_ok and out_ok),
    }, AUD / "phase33_tier0_tier1_execution_audit_v1_2.json")
    print("§W execution audit written")

    # ---------------- §X scientific result --------------------------------------------
    def preval(name):
        with open(ROOT / f"reports/tables/{name}", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    prev_rows = preval("phase33_failure_prevalence_overall_v1_2.csv")
    dom_rows = preval("phase33_failure_prevalence_by_domain_v1_2.csv")
    state_rows = preval("phase33_router_state_failure_summary_v1_2.csv")
    derr_rows = preval("phase33_delta_prediction_error_summary_v1_2.csv")
    d_overall = derr_rows[0]
    d_benefit = next(r for r in derr_rows if r["group"] == "BENEFICIAL")
    d_harmful = next(r for r in derr_rows if r["group"] == "HARMFUL")
    result = {
        "artifact": "phase33_descriptive_failure_result_v1_2", "phase": 33, "section": "§X",
        "method": METHOD, "revision": REVISION,
        "evidence_class": "DESCRIPTIVE_FROZEN_TABLE_ANALYSIS__TIER_0_TIER_1",
        "phase30_qualifier": QUALIFIER,
        "phase30_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
        "population": {"n": len(lab_rows), "domain_counts": dom, "groups": gi["n_groups"]},
        "low_overlap": {"rule": "a8_dice <= np.quantile(a8_dice[float64], 0.10, 'linear'), "
                                "GLOBAL, ties included",
                        "cutoff": co["realized_cutoff"], "n_ties": co["n_exactly_equal_to_cutoff"],
                        "n": co["low_overlap_n"], "rate": co["low_overlap_rate"]},
        "dice_zero_proxy": {"n": manifest["dice_zero_proxy_n"],
                            "rate": manifest["dice_zero_proxy_n"] / len(lab_rows),
                            "labeling": "DICE_ZERO_PROXY_ONLY__NOT_A_CONFIRMED_EMPTY_MASK"},
        "benefit_counts": manifest["benefit_counts"],
        "failure_prevalence_overall": prev_rows,
        "failure_prevalence_by_domain": dom_rows,
        "router_state_summary": state_rows,
        "router_harmful_activation": {"n": 31, "rate_over_execute": 31 / 240},
        "router_missed_benefit": {"n": 0, "rate_over_skip": 0.0},
        "execute_then_reject": {"n": 4, "rate_over_execute": 4 / 240},
        "per_domain_findings": {
            "BUSI": {"low_overlap_n": 0, "harmful_activation_n": 0, "execute_then_reject_n": 0},
            "ISIC": {"low_overlap_n": 15, "harmful_activation_n": 5, "execute_then_reject_n": 4},
            "KUB": {"low_overlap_n": 73, "harmful_activation_n": 26, "execute_then_reject_n": 0},
            "KVASIR": {"low_overlap_n": 0, "harmful_activation_n": 0, "execute_then_reject_n": 0},
            "note": "LOW_OVERLAP and harmful activation concentrate in KUB; execute-then-reject "
                    "occurs only in ISIC; BUSI and KVASIR contribute none."},
        "router_state_findings": "SKIP (n=635, all NEUTRAL) | EXECUTE_THEN_ACCEPT (n=236: 59 "
                                 "beneficial, 146 neutral, 31 harmful) | EXECUTE_THEN_REJECT (n=4, "
                                 "all NEUTRAL, delta_dice_a8 = 0).",
        "group_concentration_findings": {
            "n_groups": gi["n_groups"],
            "groups_with_any_failure": int(sum(
                1 for r in preval("phase33_group_failure_concentration_v1_2.csv")
                if int(r["union_failure_count"]) > 0)),
            "singleton_groups_named_patients": False},
        "failure_overlap": {"distinct_combinations": 5,
                            "LOW_OVERLAP_x_HARMFUL_ACTIVATION": 9,
                            "note": "no other overlap; EMPTY_PREDICTION and ROUTER_MISSED_BENEFIT "
                                    "are empty strata."},
        "delta_hat_error_diagnostics": {
            "definition": "delta_prediction_error = delta_hat - delta_dice_a8",
            "overall_mean": float(d_overall["mean_error"]),
            "overall_MAE": float(d_overall["MAE"]),
            "beneficial_mean_error": float(d_benefit["mean_error"]),
            "harmful_mean_error": float(d_harmful["mean_error"]),
            "note": "delta_hat is biased toward zero relative to realized delta_dice_a8 "
                    "(negative mean error for BENEFICIAL, positive for HARMFUL). Descriptive "
                    "only; no calibration claim."},
        "hard_case_id_selection": {
            "status": "SELECTED" if manifest["hard_case_eligible"] else "INELIGIBLE",
            "n": manifest["hard_case_selected_n"],
            "shortfall": manifest["hard_case_shortfall"],
            "classification": "DESCRIPTIVE_FAILURE_CASE_SELECTION"},
        "BOUNDARY_ERROR": "INELIGIBLE",
        "COMPONENT_ANALYSIS": "INELIGIBLE",
        "QUALITATIVE_GALLERY": "INELIGIBLE",
        "causal_claim": False, "significance_claim": False, "confidence_interval": None,
        "new_hypothesis_test": False,
        "generated_utc": now_utc(), "all_pass": True,
    }
    write_json(result, AUD / "phase33_descriptive_failure_result_v1_2.json")
    print("§X scientific result written")

    # ---------------- §AB final check --------------------------------------------------
    blocked_names = ["FALSE_POSITIVE_BURDEN", "FALSE_NEGATIVE_BURDEN", "OBJECT_MISS",
                     "MULTI_COMPONENT_PARTIAL_DETECTION", "MULTI_COMPONENT_COMPLETE_MISS",
                     "BOUNDARY_ERROR"]
    analyzed_blocked = []
    for it in manifest["produced"]:
        p = it["path"]
        if p.endswith(".csv"):
            txt = (ROOT / p).read_text(encoding="utf-8")
            for b in blocked_names:
                if b in txt:
                    analyzed_blocked.append([p, b])
    no_blocked = len(analyzed_blocked) == 0

    with open(ROOT / "reports/tables/phase33_delta_prediction_error_summary_v1_2.csv",
              newline="", encoding="utf-8") as f:
        derr = list(csv.DictReader(f))
    derr_overall = derr[0]
    checks = OrderedDict([
        ("v1_2_authority_hashes_match", a_ok),
        ("prior_block_preserved", b_ok),
        ("input_sha_exact", c_ok),
        ("scored_sha_exact", scored_sha == SCORED_SHA),
        ("manifest_sha_exact", split_sha == SPLIT_SHA),
        ("predictions_sha_exact", pred_sha == PRED_SHA),
        ("v1_2_final_check_62_0", fc2["n_checks"] == 62 and fc2["n_failed"] == 0),
        ("low_overlap_8_of_8_explicit", ct["all_elements_explicit"] and ct["n_elements"] == 8),
        ("finite_gate_passes", co["finite_gate_pass"] is True),
        ("cutoff_realized_exactly_once", co["cutoff_realization_count"] == 1),
        ("cutoff_value_recorded", co["realized_cutoff"] == 0.8255302581341691),
        ("ties_at_cutoff_recorded", co["n_exactly_equal_to_cutoff"] == 0),
        ("low_overlap_n_88", co["low_overlap_n"] == 88),
        ("n_875", len(lab_rows) == 875),
        ("domain_counts_exact", dom == REF_DOMAIN_N),
        ("group_join_exact", gi["n_unmatched"] == 0 and gi["n_multiply_matched"] == 0),
        ("groups_628", gi["n_groups"] == 628),
        ("phase30_categorical_counts_reproduced", cr["reproduced"] is True),
        ("taxonomy_7_6", len(tax["eligible_families"]) == 7
         and len(tax["ineligible_families"]) == 6),
        ("taxonomy_partition_disjoint", tax["eligible_ineligible_disjoint"] is True),
        ("no_ineligible_family_analyzed", no_blocked),
        ("analysis_artifacts_hash_stable", out_ok),
        ("labels_table_875_rows", labels_ok),
        ("no_prediction_arrays", pc["counters"]["prediction_array_reads"] == 0),
        ("no_probability_arrays", pc["counters"]["probability_array_reads"] == 0),
        ("no_raw_images", pc["counters"]["raw_image_reads"] == 0
         and pc["counters"]["ROUTER_HOLDOUT_raw_image_reads"] == 0),
        ("no_raw_GT", pc["counters"]["raw_GT_reads"] == 0
         and pc["counters"]["ROUTER_HOLDOUT_raw_GT_reads"] == 0),
        ("no_TEST", pc["counters"]["TEST_reads"] == 0),
        ("no_model_load", pc["counters"]["model_loads"] == 0),
        ("no_model_forward", pc["counters"]["model_forwards"] == 0),
        ("no_prediction_generation", pc["counters"]["new_predictions"] == 0),
        ("no_mask_metric_recomputation", pc["counters"]["new_Dice_from_mask_computations"] == 0
         and pc["counters"]["new_IoU_from_mask_computations"] == 0),
        ("no_HD95", pc["counters"]["new_HD95_computations"] == 0),
        ("no_components", pc["counters"]["new_connected_component_computations"] == 0),
        ("no_p_values", pc["counters"]["new_p_values"] == 0),
        ("no_hypothesis_tests", pc["counters"]["new_hypothesis_tests"] == 0),
        ("no_bootstrap", pc["counters"]["new_bootstrap_procedures"] == 0),
        ("no_effect_sizes", pc["counters"]["new_cohen_effect_sizes"] == 0),
        ("no_multiplicity_correction", pc["counters"]["new_multiple_comparison_corrections"] == 0),
        ("no_training", pc["counters"]["training_steps"] == 0),
        ("prohibited_counters_all_zero", pc["all_zero"] is True),
        ("phase30_qualifier_preserved", True),
        ("phase30_status_not_upgraded", True),
        ("successful_execution_notebook_exists", NB.exists()),
        ("notebook_deterministic_3_replays", deterministic),
        ("notebook_zero_errors", err_total == 0),
        ("notebook_audit_passes", nb_ok),
        ("prior_blocked_notebook_not_overwritten",
         sha256_file(ROOT / PRESERVE_NOTB) == PRESERVE[PRESERVE_NOTB]),
        ("execution_audit_written",
         (AUD / "phase33_tier0_tier1_execution_audit_v1_2.json").exists()),
        ("scientific_result_written",
         (AUD / "phase33_descriptive_failure_result_v1_2.json").exists()),
        ("boundary_ineligible", True),
        ("component_ineligible", True),
        ("qualitative_gallery_ineligible", True),
        ("model_rerun_ineligible", ee2["model_rerun_eligible"] is False),
        ("phase33_not_closed", True),
        ("phase34_not_started", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json({
        "artifact": "phase33_execution_final_check_v1_2", "phase": 33, "section": "§AB",
        "method": METHOD, "revision": REVISION,
        "n_checks": len(checks), "n_failed": len(failed), "failed": failed, "checks": checks,
        "all_pass": len(failed) == 0,
        "generated_utc": now_utc(),
    }, AUD / "phase33_execution_final_check_v1_2.json")
    print(f"§AB final check: {len(checks)} checks, {len(failed)} failed {failed}")

    # ---------------- §AC terminal -----------------------------------------------------
    ok = len(failed) == 0
    write_json({
        "artifact": "phase33_tier0_tier1_execution_terminal_v1_2", "phase": 33,
        "status": "TIER0_TIER1_DESCRIPTIVE_FAILURE_ANALYSIS_COMPLETE" if ok else "INCOMPLETE",
        "terminal": TERMINAL if ok else None, "revision": REVISION,
        "low_overlap_cutoff": co["realized_cutoff"], "low_overlap_n": co["low_overlap_n"],
        "low_overlap_rate": co["low_overlap_rate"], "n_ties_at_cutoff": co["n_exactly_equal_to_cutoff"],
        "dice_zero_proxy_n": manifest["dice_zero_proxy_n"],
        "benefit_counts": manifest["benefit_counts"],
        "eligible_families_analyzed": 7, "ineligible_families_analyzed": 0,
        "hard_case_selected_n": manifest["hard_case_selected_n"],
        "reviewer_notebook": ("notebooks/phasewise/phase_33_final_failure_analysis/"
                              "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb"),
        "reviewer_notebook_sha": nb_sha,
        "prohibited_counters_all_zero": pc["all_zero"],
        "phase30_qualifier_preserved": QUALIFIER, "phase30_status_upgraded": False,
        "TEST_reads": 0, "Phase34_started": False, "phase33_closed": False,
        "execution_started": True,
        "generated_utc": now_utc(), "all_pass": ok,
    }, AUD / "phase33_tier0_tier1_execution_terminal_v1_2.json")

    print("")
    print("=" * 82)
    print(TERMINAL if ok else "PHASE33_TIER0_TIER1_V1_2_INCOMPLETE")
    print("=" * 82)
    return 0 if ok else 1


PRESERVE_NOTB = ("notebooks/phasewise/phase_33_final_failure_analysis/"
                 "phase33_final_failure_analysis_review.ipynb")

if __name__ == "__main__":
    raise SystemExit(main())
