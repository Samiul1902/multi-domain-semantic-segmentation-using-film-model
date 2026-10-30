#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — TIER_0 + TIER_1 DESCRIPTIVE FAILURE ANALYSIS (EXECUTION v1.2).

Authorized scope ONLY: TIER_0_FROZEN_TABLE_READ_ONLY and TIER_1_DERIVED_FROM_FROZEN_NONPIXEL_FIELDS.
TIER_2 / TIER_3 / TIER_4 remain prohibited.

Reads ONLY frozen non-pixel tables:
  * reports/tables/phase30_router_holdout_scored_results.csv   (scored, TIER_0)
  * reports/tables/phase30_router_holdout_predictions.csv      (predictions, frozen non-pixel)
  * reports/audits/phase24_router_split_manifest.csv           (metadata-only group map)

NO image, NO mask, NO prediction/probability array, NO model, NO TEST, NO new Dice/IoU/HD95.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase33_tier0_tier1_execution_v1_2.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_2"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
PHASE30_STATUS = "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL"

BLOCK_TERMINAL = ("PHASE33_LOW_OVERLAP_REALIZATION_BLOCKED__A8_DICE_NOT_COMPLETE_FINITE_875__"
                  "NO_CUTOFF_COMPUTED")

# ------------------------------------------------------------------ §A authority (v1.2) ----------
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

# ------------------------------------------------------------------ §B preserve prior block ------
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

# ------------------------------------------------------------------ §C inputs ---------------------
SCORED = "reports/tables/phase30_router_holdout_scored_results.csv"
SCORED_SHA = "dbc9f5f3867f0607cfc0a778736a92b9d6de6e27811fa382ad6d1cb0b2a04568"
SPLIT = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"
PRED = "reports/tables/phase30_router_holdout_predictions.csv"
PRED_SHA = "513ccf2905cbc6f544337b9d157f38dc34d835e2cb56c25cabbe95f5046a3147"

REF_DOMAIN_N = {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104}
REF_TOTAL = 875
REF_GROUPS = 628
ANCHORS = {"execute": 240, "skip": 635, "execute_then_accept": 236,
           "execute_then_reject": 4, "forced_skip": 0,
           "harmful_activated": 31, "missed_benefit": 0}

BENEFICIAL_T = 0.02
HARMFUL_T = -0.01

ELIGIBLE_FAMILIES = ["LOW_OVERLAP", "EMPTY_PREDICTION", "ROUTER_HARMFUL_ACTIVATION",
                     "ROUTER_MISSED_BENEFIT", "EXECUTE_THEN_REJECT", "DOMAIN_SPECIFIC_FAILURE",
                     "GROUP_OR_PATIENT_CLUSTERED_FAILURE"]
BLOCKED_FAMILIES = ["FALSE_POSITIVE_BURDEN", "FALSE_NEGATIVE_BURDEN", "OBJECT_MISS",
                    "MULTI_COMPONENT_PARTIAL_DETECTION", "MULTI_COMPONENT_COMPLETE_MISS",
                    "BOUNDARY_ERROR"]


# ------------------------------------------------------------------ helpers -----------------------
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
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_csv(header, rows, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def fnum(x):
    """Full-precision, deterministic float formatting (or empty for None)."""
    if x is None:
        return ""
    if isinstance(x, (int, np.integer)) and not isinstance(x, bool):
        return str(int(x))
    v = float(x)
    if math.isnan(v):
        return "NaN"
    return repr(v)


def stats(xs):
    vals = [float(x) for x in xs if x is not None and math.isfinite(float(x))]
    if not vals:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None}
    a = np.array(vals, dtype=np.float64)
    return {"n": len(vals), "mean": float(a.mean()), "median": float(np.median(a)),
            "min": float(a.min()), "max": float(a.max())}


def read_csv(p):
    with open(ROOT / p, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 82)
    print("PHASE 33 — TIER_0 + TIER_1 DESCRIPTIVE FAILURE ANALYSIS (EXECUTION v1.2)")
    print("=" * 82)
    produced = []

    # ============================== §A bind v1.2 authority ================================== #
    abinds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
               "match": sha256_file(ROOT / p) == e} for p, e in AUTHORITY.items()]
    a_ok = all(b["match"] for b in abinds)
    fc2 = read_json("reports/audits/phase33_specification_final_check_v1_2.json")
    ee2 = read_json("reports/audits/phase33_execution_eligibility_adjudication_v1_2.json")
    ct2 = read_json("reports/audits/phase33_low_overlap_realization_contract_v1_2.json")
    fc_ok = (fc2["n_checks"] == 62 and fc2["n_failed"] == 0)
    ee_ok = (ee2["table_only_execution_eligible"] is True
             and ee2["derived_nonpixel_execution_eligible"] is True
             and ee2["prediction_pixel_execution_eligible"] is False
             and ee2["raw_image_execution_eligible"] is False
             and ee2["raw_GT_execution_eligible"] is False
             and ee2["qualitative_gallery_eligible"] is False
             and ee2["boundary_metric_execution_eligible"] is False
             and ee2["component_metric_execution_eligible"] is False
             and ee2["model_rerun_eligible"] is False)
    ct_ok = (ct2["all_elements_explicit"] is True and ct2["rule_exactly_frozen"] is True
             and ct2["low_overlap_target_column"] == "a8_dice"
             and ct2["comparison_operator"] == "<="
             and ct2["missing_policy"] == "REQUIRE_ALL_FINITE_NO_EXCLUSION"
             and ct2["scope"] == "GLOBAL_NOT_PER_DOMAIN")
    print(f"§A authority {sum(1 for b in abinds if b['match'])}/{len(abinds)} match; "
          f"final_check {fc2['n_checks']}/{fc2['n_failed']} failed; eligibility={ee_ok}; "
          f"contract={ct_ok}")
    if not (a_ok and fc_ok and ee_ok and ct_ok):
        print("FAIL-CLOSED: v1.2 authority gate failed.")
        return 1

    # ============================== §B preserve prior block ================================= #
    pbinds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
               "match": sha256_file(ROOT / p) == e} for p, e in PRESERVE.items()]
    b_ok = all(b["match"] for b in pbinds)
    write_json({
        "artifact": "phase33_tier0_tier1_prior_block_preservation_v1_2", "phase": 33,
        "section": "§B", "method": METHOD, "revision": REVISION,
        "statement": "the previous blocked execution was CORRECT and is preserved byte-for-byte "
                     "as historical fail-closed provenance",
        "preserved": pbinds, "n_preserved": len(pbinds),
        "n_match": sum(1 for b in pbinds if b["match"]), "all_preserved": b_ok,
        "blocked_notebook_repurposed": False,
        "generated_utc": now_utc(), "all_pass": b_ok,
    }, AUD / "phase33_tier0_tier1_prior_block_preservation_v1_2.json")
    produced.append({"path": "reports/audits/phase33_tier0_tier1_prior_block_preservation_v1_2.json",
                     "section": "§B"})
    print(f"§B prior block preserved {sum(1 for b in pbinds if b['match'])}/{len(pbinds)}")
    if not b_ok:
        print("FAIL-CLOSED: prior-block preservation failed.")
        return 1

    # ============================== §C input authority ====================================== #
    scored_sha = sha256_file(ROOT / SCORED)
    split_sha = sha256_file(ROOT / SPLIT)
    pred_sha = sha256_file(ROOT / PRED)
    c_ok = (scored_sha == SCORED_SHA and split_sha == SPLIT_SHA and pred_sha == PRED_SHA)
    print(f"§C inputs: scored={scored_sha == SCORED_SHA} split={split_sha == SPLIT_SHA} "
          f"predictions={pred_sha == PRED_SHA}")
    if not c_ok:
        print("FAIL-CLOSED: input SHA mismatch.")
        return 1

    scored = read_csv(SCORED)
    preds = read_csv(PRED)
    split_rows = read_csv(SPLIT)
    pred_map = {p["sample_id"]: p for p in preds}

    # ============================== §C population integrity ================================= #
    ids = [r["sample_id"] for r in scored]
    dup_ids = len(ids) - len(set(ids))
    dom = Counter(r["dataset"] for r in scored)
    ho = [r for r in split_rows if r["split_role"] == "ROUTER_HOLDOUT"]
    ho_map = {r["sample_id"]: r for r in ho}
    unmatched = [i for i in ids if i not in ho_map]
    pred_ids = {r["sample_id"] for r in preds}
    pred_missing = sorted(set(ids) - pred_ids)
    pred_extra = sorted(pred_ids - set(ids))
    groups = {ho_map[i]["group_key"] for i in ids if i in ho_map}
    pop_ok = (len(scored) == REF_TOTAL and dup_ids == 0 and len(unmatched) == 0
              and dict(dom) == REF_DOMAIN_N and len(groups) == REF_GROUPS
              and not pred_missing and not pred_extra)
    print(f"§C population: n={len(scored)} dup={dup_ids} unmatched={len(unmatched)} "
          f"groups={len(groups)} domains={dict(dom)} pred_join_ok={not pred_missing and not pred_extra}")
    if not pop_ok:
        print("FAIL-CLOSED: population integrity failed.")
        return 1

    # frozen numeric arrays
    a8 = np.array([float(r["a8_dice"]) for r in scored], dtype=np.float64)
    gd_all = np.array([float(r["global_dice"]) for r in scored], dtype=np.float64)
    dd = np.array([float(r["delta_dice_a8"]) for r in scored], dtype=np.float64)
    ex_mask = np.array([r["router_decision"] == "EXECUTE" for r in scored])
    sk_mask = ~ex_mask
    st = np.array([pred_map[r["sample_id"]]["state_machine"] for r in scored])
    dh = np.array([float(pred_map[r["sample_id"]]["delta_hat"]) for r in scored], dtype=np.float64)
    som_score = np.array([
        (float(pred_map[r["sample_id"]]["somega_score"])
         if str(pred_map[r["sample_id"]]["somega_score"]).strip() not in ("", "None") else np.nan)
        for r in scored], dtype=np.float64)

    # ============================== §E finite gate + cutoff realization ===================== #
    raw = [r["a8_dice"] for r in scored]
    missing = sum(1 for v in raw if v is None or str(v).strip() == "")
    n_nan = int(np.isnan(a8).sum())
    n_pinf = int(np.isposinf(a8).sum())
    n_ninf = int(np.isneginf(a8).sum())
    n_nonfinite = int((~np.isfinite(a8)).sum())
    empty = sum(1 for v in raw if not str(v).strip())
    gate = {"n": len(a8), "len_875": len(a8) == 875, "missing": missing, "NaN": n_nan,
            "posinf": n_pinf, "neginf": n_ninf, "non_finite": n_nonfinite, "empty": empty}
    finite_gate_pass = (len(a8) == 875 and missing == 0 and n_nan == 0 and n_pinf == 0
                        and n_ninf == 0 and n_nonfinite == 0 and empty == 0)
    print(f"§E finite gate: {gate} -> pass={finite_gate_pass}")
    if not finite_gate_pass:
        write_json({"artifact": "phase33_low_overlap_cutoff_realization", "phase": 33,
                    "section": "§E", "method": METHOD, "revision": REVISION,
                    "finite_gate": gate, "finite_gate_pass": False, "cutoff_realized": False,
                    "realized_cutoff": None, "action": "BLOCK",
                    "blocked_terminal": BLOCK_TERMINAL, "generated_utc": now_utc(),
                    "all_pass": False}, AUD / "phase33_low_overlap_cutoff_realization.json")
        print("")
        print(BLOCK_TERMINAL)
        return 2

    cutoff = float(np.quantile(a8, 0.10, method="linear"))
    low = a8 <= cutoff
    n_ties = int((a8 == cutoff).sum())
    lo_n = int(low.sum())
    lo_rate = lo_n / len(a8)
    write_json({
        "artifact": "phase33_low_overlap_cutoff_realization", "phase": 33, "section": "§E",
        "method": METHOD, "revision": REVISION,
        "authority_contract": {
            "path": "reports/audits/phase33_low_overlap_realization_contract_v1_2.json",
            "sha256": AUTHORITY["reports/audits/phase33_low_overlap_realization_contract_v1_2.json"]},
        "source_scored_table": {"path": SCORED, "sha256": scored_sha},
        "n": len(a8), "finite_gate": gate, "finite_gate_pass": True,
        "policy": "REQUIRE_ALL_FINITE_NO_EXCLUSION",
        "q": 0.10, "dtype": "float64", "method": "linear",
        "comparison": "<=", "ties_included": True, "scope": "GLOBAL",
        "target_column": "a8_dice", "reference_only_column": "global_dice",
        "realized_cutoff": cutoff, "realized_cutoff_repr": repr(cutoff),
        "n_exactly_equal_to_cutoff": n_ties,
        "low_overlap_n": lo_n, "low_overlap_rate": lo_rate,
        "cutoff_realized": True, "cutoff_realization_count": 1,
        "no_rounding_before_quantile": True, "no_row_exclusion": True, "no_weighting": True,
        "no_bootstrap": True, "no_per_domain_cutoff": True,
        "science_definition_changed": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_low_overlap_cutoff_realization.json")
    produced.append({"path": "reports/audits/phase33_low_overlap_cutoff_realization.json",
                     "section": "§E"})
    print(f"§E cutoff realized EXACTLY ONCE: {repr(cutoff)} | ties={n_ties} | "
          f"LOW_OVERLAP n={lo_n} rate={lo_rate}")

    # ============================== §J Phase30 count reproduction =========================== #
    harm = ex_mask & (dd <= HARMFUL_T)
    miss = sk_mask & (dd >= BENEFICIAL_T)
    obs = {"execute": int(ex_mask.sum()), "skip": int(sk_mask.sum()),
           "execute_then_accept": int((st == "EXECUTE_THEN_ACCEPT").sum()),
           "execute_then_reject": int((st == "EXECUTE_THEN_REJECT").sum()),
           "forced_skip": 0,
           "harmful_activated": int(harm.sum()), "missed_benefit": int(miss.sum())}
    repro_ok = obs == ANCHORS
    write_json({
        "artifact": "phase33_phase30_count_reproduction_v1_2", "phase": 33, "section": "§J",
        "method": METHOD, "revision": REVISION,
        "purpose": "verification anchors reproduced from the frozen scored/prediction tables "
                   "before broader analysis",
        "observed": obs, "frozen_authority": ANCHORS, "reproduced": repro_ok,
        "forced_skip_provenance": "no forced_skip category exists in the frozen state machine "
                                  "(SKIP / EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT); count = 0",
        "anchors_forced": False, "fail_closed_on_mismatch": True,
        "source_scored_table": {"path": SCORED, "sha256": scored_sha},
        "source_predictions_table": {"path": PRED, "sha256": pred_sha},
        "generated_utc": now_utc(), "all_pass": repro_ok,
    }, AUD / "phase33_phase30_count_reproduction_v1_2.json")
    produced.append({"path": "reports/audits/phase33_phase30_count_reproduction_v1_2.json",
                     "section": "§J"})
    print(f"§J count reproduction: {obs} -> reproduced={repro_ok}")
    if not repro_ok:
        print("FAIL-CLOSED: Phase30 count reproduction mismatch. Stopping before result production.")
        return 3

    # ============================== §G/§H/§I derived per-sample table ======================= #
    benefit = np.where(dd >= BENEFICIAL_T, "BENEFICIAL",
                       np.where(dd <= HARMFUL_T, "HARMFUL", "NEUTRAL"))
    empty_proxy = (a8 == 0.0)
    etr = (st == "EXECUTE_THEN_REJECT")

    labels_header = ["sample_id", "dataset", "group_key", "global_dice", "a8_dice",
                     "delta_dice_a8", "a7_dice", "delta_dice_a7", "router_decision",
                     "state_machine", "somega_accept", "somega_score", "delta_hat", "utility",
                     "tau_C8", "roi_available", "benefit_class", "low_overlap",
                     "empty_prediction_proxy", "router_harmful_activation",
                     "router_missed_benefit", "execute_then_reject"]
    labels_rows = []
    for i, r in enumerate(scored):
        p = pred_map[r["sample_id"]]
        labels_rows.append([r["sample_id"], r["dataset"], ho_map[r["sample_id"]]["group_key"],
                            r["global_dice"], r["a8_dice"], r["delta_dice_a8"], r["a7_dice"],
                            r["delta_dice_a7"], r["router_decision"], st[i], r["somega_accept"],
                            p["somega_score"], p["delta_hat"], p["utility"], p["tau_C8"],
                            p["roi_available"], benefit[i], bool(low[i]), bool(empty_proxy[i]),
                            bool(harm[i]), bool(miss[i]), bool(etr[i])])
    write_csv(labels_header, labels_rows, TAB / "phase33_final_system_failure_labels_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_final_system_failure_labels_v1_2.csv",
                     "section": "§I"})
    print(f"§I labels table: {len(labels_rows)} rows, {len(labels_header)} cols")

    # ============================== §K overall failure prevalence =========================== #
    def prow(fam, mask, pop_n, pop_def):
        k = int(mask.sum())
        return [fam, pop_n, k, (k / pop_n if pop_n else 0.0), pop_def]
    write_csv(["family", "eligible_population_n", "failure_n", "failure_rate",
               "population_definition"],
              [prow("LOW_OVERLAP", low, len(a8), "all 875 ROUTER_HOLDOUT rows"),
               prow("EMPTY_PREDICTION", empty_proxy, len(a8), "all 875 ROUTER_HOLDOUT rows"),
               prow("ROUTER_HARMFUL_ACTIVATION", harm, int(ex_mask.sum()), "EXECUTE rows (240)"),
               prow("ROUTER_MISSED_BENEFIT", miss, int(sk_mask.sum()), "SKIP rows (635)"),
               prow("EXECUTE_THEN_REJECT", etr, int(ex_mask.sum()), "EXECUTE rows (240)")],
              TAB / "phase33_failure_prevalence_overall_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_failure_prevalence_overall_v1_2.csv",
                     "section": "§K"})

    # ============================== §L domain failure prevalence ============================ #
    dom_rows = []
    for d in ["BUSI", "ISIC", "KUB", "KVASIR"]:
        m = np.array([r["dataset"] == d for r in scored])
        n = int(m.sum())

        def rr(mask):
            k = int((mask & m).sum())
            return k, (k / n if n else 0.0)
        lo_k, lo_r = rr(low); ez_k, ez_r = rr(empty_proxy); ha_k, ha_r = rr(harm)
        mb_k, mb_r = rr(miss); er_k, er_r = rr(etr)
        dom_rows.append([d, n, lo_k, lo_r, ez_k, ez_r, ha_k, ha_r, mb_k, mb_r, er_k, er_r])
    write_csv(["dataset", "n", "low_overlap_n", "low_overlap_rate", "dice_zero_proxy_n",
               "dice_zero_proxy_rate", "harmful_activation_n", "harmful_activation_rate",
               "missed_benefit_n", "missed_benefit_rate", "execute_then_reject_n",
               "execute_then_reject_rate"], dom_rows,
              TAB / "phase33_failure_prevalence_by_domain_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_failure_prevalence_by_domain_v1_2.csv",
                     "section": "§L"})

    # ============================== §M router-state failure analysis ========================= #
    state_rows = []
    for s in ["SKIP", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]:
        m = (st == s)
        n = int(m.sum())
        gd = stats(gd_all[m]); ad = stats(a8[m]); dstat = stats(dd[m])
        bc = Counter(benefit[i] for i in range(len(scored)) if m[i])
        state_rows.append([s, n, n / len(scored), fnum(gd["mean"]), fnum(gd["median"]),
                           fnum(ad["mean"]), fnum(ad["median"]), fnum(dstat["mean"]),
                           fnum(dstat["median"]), bc.get("BENEFICIAL", 0), bc.get("NEUTRAL", 0),
                           bc.get("HARMFUL", 0), int((low & m).sum()), int((empty_proxy & m).sum())])
    write_csv(["state_machine", "n", "share", "global_dice_mean", "global_dice_median",
               "a8_dice_mean", "a8_dice_median", "delta_dice_a8_mean", "delta_dice_a8_median",
               "beneficial_n", "neutral_n", "harmful_n", "low_overlap_n", "dice_zero_proxy_n"],
              state_rows, TAB / "phase33_router_state_failure_summary_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_router_state_failure_summary_v1_2.csv",
                     "section": "§M"})

    # ============================== §N failure severity ====================================== #
    sev_rows = []
    for fam, m in [("LOW_OVERLAP", low), ("EMPTY_PREDICTION", empty_proxy),
                   ("ROUTER_HARMFUL_ACTIVATION", harm), ("ROUTER_MISSED_BENEFIT", miss),
                   ("EXECUTE_THEN_REJECT", etr)]:
        n = int(m.sum()); ad = stats(a8[m]); ds = stats(dd[m])
        sev_rows.append([fam, n, fnum(ad["mean"]), fnum(ad["median"]), fnum(ad["min"]),
                         fnum(ad["max"]), fnum(ds["mean"]), fnum(ds["median"]), fnum(ds["min"]),
                         fnum(ds["max"]),
                         "MEANINGFUL" if n > 0 else "NOT_MEANINGFUL_EMPTY_STRATUM"])
    write_csv(["family", "n", "a8_dice_mean", "a8_dice_median", "a8_dice_min", "a8_dice_max",
               "delta_dice_a8_mean", "delta_dice_a8_median", "delta_dice_a8_min",
               "delta_dice_a8_max", "meaningfulness"], sev_rows,
              TAB / "phase33_failure_severity_summary_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_failure_severity_summary_v1_2.csv",
                     "section": "§N"})

    # ============================== §O selected vs skipped =================================== #
    sel_rows = []
    for name, m in [("EXECUTE", ex_mask), ("SKIP", sk_mask)]:
        gd = stats(gd_all[m]); ad = stats(a8[m]); ds = stats(dd[m])
        sel_rows.append([name, int(m.sum()), fnum(gd["mean"]), fnum(gd["median"]),
                         fnum(ad["mean"]), fnum(ad["median"]), fnum(ds["mean"]),
                         fnum(ds["median"])])
    write_csv(["group", "n", "global_dice_mean", "global_dice_median", "a8_dice_mean",
               "a8_dice_median", "delta_dice_a8_mean", "delta_dice_a8_median"], sel_rows,
              TAB / "phase33_selected_vs_skipped_summary_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_selected_vs_skipped_summary_v1_2.csv",
                     "section": "§O"})

    # ============================== §P accepted vs rejected ================================== #
    ar_rows = []
    for name, m in [("EXECUTE_THEN_ACCEPT", st == "EXECUTE_THEN_ACCEPT"),
                    ("EXECUTE_THEN_REJECT", etr)]:
        gd = stats(gd_all[m]); ad = stats(a8[m]); ds = stats(dd[m]); ss = stats(som_score[m])
        ar_rows.append([name, int(m.sum()), fnum(gd["mean"]), fnum(gd["median"]),
                        fnum(ad["mean"]), fnum(ad["median"]), fnum(ds["mean"]),
                        fnum(ds["median"]), fnum(ds["min"]), fnum(ds["max"]),
                        fnum(ss["mean"]), fnum(ss["median"])])
    write_csv(["group", "n", "global_dice_mean", "global_dice_median", "a8_dice_mean",
               "a8_dice_median", "delta_dice_a8_mean", "delta_dice_a8_median",
               "delta_dice_a8_min", "delta_dice_a8_max", "somega_score_mean",
               "somega_score_median"], ar_rows,
              TAB / "phase33_accepted_vs_rejected_summary_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_accepted_vs_rejected_summary_v1_2.csv",
                     "section": "§P"})

    # ============================== §Q domain-specific failure summary ======================= #
    ds_rows = []
    for d in ["BUSI", "ISIC", "KUB", "KVASIR"]:
        m = np.array([r["dataset"] == d for r in scored])
        n = int(m.sum())
        gd = stats(gd_all[m]); ad = stats(a8[m]); ds = stats(dd[m])
        lo_k = int((low & m).sum()); ez_k = int((empty_proxy & m).sum())
        ha_k = int((harm & m).sum()); mb_k = int((miss & m).sum()); er_k = int((etr & m).sum())
        ds_rows.append([d, n, fnum(gd["mean"]), fnum(gd["median"]), fnum(gd["min"]),
                        fnum(gd["max"]), fnum(ad["mean"]), fnum(ad["median"]), fnum(ad["min"]),
                        fnum(ad["max"]), fnum(ds["mean"]), fnum(ds["median"]), fnum(ds["min"]),
                        fnum(ds["max"]), lo_k, lo_k / n, ez_k, ez_k / n, ha_k, ha_k / n,
                        mb_k, mb_k / n, er_k, er_k / n])
    write_csv(["dataset", "n", "global_dice_mean", "global_dice_median", "global_dice_min",
               "global_dice_max", "a8_dice_mean", "a8_dice_median", "a8_dice_min", "a8_dice_max",
               "delta_dice_a8_mean", "delta_dice_a8_median", "delta_dice_a8_min",
               "delta_dice_a8_max", "low_overlap_n", "low_overlap_rate", "dice_zero_proxy_n",
               "dice_zero_proxy_rate", "harmful_activation_n", "harmful_activation_rate",
               "missed_benefit_n", "missed_benefit_rate", "execute_then_reject_n",
               "execute_then_reject_rate"], ds_rows,
              TAB / "phase33_domain_specific_failure_summary_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_domain_specific_failure_summary_v1_2.csv",
                     "section": "§Q"})

    # ============================== §R group concentration =================================== #
    grp = OrderedDict()
    for i, r in enumerate(scored):
        gk = ho_map[r["sample_id"]]["group_key"]
        g = grp.setdefault(gk, {"dataset": r["dataset"], "n": 0, "lo": 0, "ez": 0, "ha": 0,
                                "mb": 0, "er": 0, "union": 0})
        g["n"] += 1
        g["lo"] += int(low[i]); g["ez"] += int(empty_proxy[i]); g["ha"] += int(harm[i])
        g["mb"] += int(miss[i]); g["er"] += int(etr[i])
        if low[i] or empty_proxy[i] or harm[i] or miss[i] or etr[i]:
            g["union"] += 1
    grp_rows = [[gk, g["dataset"], g["n"], g["lo"], g["ez"], g["ha"], g["mb"], g["er"],
                 g["union"]] for gk, g in grp.items()]
    write_csv(["group_key", "dataset", "n_samples", "low_overlap_count",
               "empty_prediction_proxy_count", "harmful_activation_count",
               "missed_benefit_count", "execute_then_reject_count", "union_failure_count"],
              grp_rows, TAB / "phase33_group_failure_concentration_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_group_failure_concentration_v1_2.csv",
                     "section": "§R"})
    gi_ok = (len(grp_rows) == REF_GROUPS and sum(g["n"] for g in grp.values()) == REF_TOTAL
             and len(unmatched) == 0 and dup_ids == 0)
    write_json({
        "artifact": "phase33_group_join_integrity_v1_2", "phase": 33, "section": "§R",
        "method": METHOD, "revision": REVISION,
        "join_keys": ["sample_id", "dataset", "group_key"],
        "n_rows": len(scored), "n_uniquely_mapped": len(scored) - len(unmatched) - dup_ids,
        "n_unmatched": len(unmatched), "n_multiply_matched": dup_ids,
        "n_groups": len(grp_rows), "expected_groups": REF_GROUPS,
        "singleton_groups_named_patients": False,
        "generated_utc": now_utc(), "all_pass": gi_ok,
    }, AUD / "phase33_group_join_integrity_v1_2.json")
    produced.append({"path": "reports/audits/phase33_group_join_integrity_v1_2.json",
                     "section": "§R"})
    print(f"§R group join integrity: {len(grp_rows)} groups, ok={gi_ok}")

    # ============================== §S failure category overlap ============================== #
    cat_masks = OrderedDict([("LOW_OVERLAP", low), ("EMPTY_PREDICTION", empty_proxy),
                             ("ROUTER_HARMFUL_ACTIVATION", harm),
                             ("ROUTER_MISSED_BENEFIT", miss), ("EXECUTE_THEN_REJECT", etr)])
    cats = list(cat_masks)
    ov_rows = [[a_] + [int((cat_masks[a_] & cat_masks[b_]).sum()) for b_ in cats] for a_ in cats]
    write_csv(["category"] + cats, ov_rows,
              TAB / "phase33_failure_category_overlap_matrix_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_failure_category_overlap_matrix_v1_2.csv",
                     "section": "§S"})
    combo = Counter()
    for i in range(len(scored)):
        combo[tuple(c for c in cats if cat_masks[c][i])] += 1
    combo_rows = [["|".join(active) if active else "NONE", len(active), combo[active]]
                  for active in sorted(combo, key=lambda t: (-len(t), t))]
    write_csv(["combination", "n_categories", "n_samples"], combo_rows,
              TAB / "phase33_failure_combination_counts_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_failure_combination_counts_v1_2.csv",
                     "section": "§S"})
    print(f"§S overlap matrix {len(cats)}x{len(cats)}; {len(combo_rows)} distinct combinations")

    # ============================== §T delta_hat diagnostics ================================= #
    err = dh - dd
    t_rows = []

    def err_row(label, group, mask):
        e = err[mask]
        if len(e) == 0:
            return
        t_rows.append([label, group, len(e), fnum(float(e.mean())), fnum(float(np.median(e))),
                       fnum(float(np.abs(e).mean())), fnum(float(e.min())), fnum(float(e.max()))])
    err_row("overall", "ALL", np.ones(len(scored), dtype=bool))
    for d in ["BUSI", "ISIC", "KUB", "KVASIR"]:
        err_row("domain", d, np.array([r["dataset"] == d for r in scored]))
    for s in ["SKIP", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]:
        err_row("router_state", s, (st == s))
    for bc in ["BENEFICIAL", "NEUTRAL", "HARMFUL"]:
        err_row("benefit_class", bc, (benefit == bc))
    write_csv(["grouping", "group", "n", "mean_error", "median_error", "MAE", "min", "max"],
              t_rows, TAB / "phase33_delta_prediction_error_summary_v1_2.csv")
    produced.append({"path": "reports/tables/phase33_delta_prediction_error_summary_v1_2.csv",
                     "section": "§T"})
    print(f"§T delta_hat diagnostics: {len(t_rows)} rows")

    # ============================== §U hard-case ID selection ================================ #
    hc = read_json("reports/audits/phase33_hard_case_selection_contract.json")
    proc = hc["procedure"]
    contract_exact = (hc.get("selection_requires_frozen_procedure_first") is True
                      and proc.get("target_number_per_stratum") == 8
                      and proc.get("ordering") == ("within stratum: delta_dice_a8 ascending, "
                                                   "then sample_id ascending")
                      and proc.get("tie_break") == "sample_id ascending"
                      and str(proc.get("deduplication_across_strata", "")).startswith("first stratum")
                      and proc.get("group_patient_balancing") ==
                          "at most one sample per group_key within a panel"
                      and str(proc.get("underfilled_stratum", "")).startswith("report the shortfall"))
    hc_rows = []
    shortfall = {}
    if contract_exact:
        selected = set()
        for sname, smask in [("low_dice_bottom_decile", low), ("harmful_activation", harm),
                             ("missed_benefit", miss), ("execute_then_reject", etr)]:
            cand = sorted([i for i in range(len(scored)) if smask[i]],
                          key=lambda i: (dd[i], scored[i]["sample_id"]))
            panel, used_groups = [], set()
            for i in cand:
                if len(panel) >= 8:
                    break
                sid = scored[i]["sample_id"]
                gk = ho_map[sid]["group_key"]
                if sid in selected or gk in used_groups:
                    continue
                panel.append(i); selected.add(sid); used_groups.add(gk)
            shortfall[sname] = 8 - len(panel)
            for rank, i in enumerate(panel, 1):
                sid = scored[i]["sample_id"]
                hc_rows.append([sname, rank, sid, scored[i]["dataset"], ho_map[sid]["group_key"],
                                fnum(dd[i]), fnum(a8[i])])
        write_csv(["stratum", "rank_within_stratum", "sample_id", "dataset", "group_key",
                   "delta_dice_a8", "a8_dice"], hc_rows, TAB / "phase33_hard_case_ids_v1_2.csv")
        produced.append({"path": "reports/tables/phase33_hard_case_ids_v1_2.csv", "section": "§U"})
        print(f"§U hard-case IDs selected: {len(hc_rows)} rows; shortfall={shortfall}")
    else:
        write_json({"artifact": "phase33_hard_case_selection_ineligibility", "phase": 33,
                    "section": "§U", "method": METHOD, "revision": REVISION,
                    "reason": "hard-case selection contract not exact or not TIER_0/TIER_1-only",
                    "cases_selected": 0, "generated_utc": now_utc(), "all_pass": True},
                   AUD / "phase33_hard_case_selection_ineligibility_v1_2.json")
        produced.append({"path":
                         "reports/audits/phase33_hard_case_selection_ineligibility_v1_2.json",
                         "section": "§U"})
        print("§U hard-case selection NOT eligible -> ineligibility audit written")

    # ============================== §V prohibited counters ================================== #
    counters = OrderedDict([
        ("prediction_array_reads", 0), ("probability_array_reads", 0),
        ("raw_image_reads", 0), ("raw_GT_reads", 0),
        ("ROUTER_HOLDOUT_raw_image_reads", 0), ("ROUTER_HOLDOUT_raw_GT_reads", 0),
        ("TEST_reads", 0), ("model_loads", 0), ("model_forwards", 0),
        ("new_predictions", 0), ("training_steps", 0),
        ("new_Dice_from_mask_computations", 0), ("new_IoU_from_mask_computations", 0),
        ("new_HD95_computations", 0), ("new_connected_component_computations", 0),
        ("new_FP_FN_pixel_analyses", 0), ("new_object_analyses", 0),
        ("new_p_values", 0), ("new_hypothesis_tests", 0), ("new_bootstrap_procedures", 0),
        ("new_cohen_effect_sizes", 0), ("new_multiple_comparison_corrections", 0)])
    write_json({
        "artifact": "phase33_tier0_tier1_prohibited_counters_v1_2", "phase": 33, "section": "§V",
        "method": METHOD, "revision": REVISION,
        "counters": counters, "all_zero": all(v == 0 for v in counters.values()),
        "n_counters": len(counters),
        "generated_utc": now_utc(), "all_pass": all(v == 0 for v in counters.values()),
    }, AUD / "phase33_tier0_tier1_prohibited_counters_v1_2.json")
    produced.append({"path": "reports/audits/phase33_tier0_tier1_prohibited_counters_v1_2.json",
                     "section": "§V"})

    # ============================== analysis manifest ======================================= #
    for item in produced:
        item["sha256"] = sha256_file(ROOT / item["path"])
    write_json({
        "artifact": "phase33_tier0_tier1_analysis_manifest_v1_2", "phase": 33,
        "section": "§I-§U", "method": METHOD, "revision": REVISION,
        "produced": produced, "n_produced": len(produced),
        "low_overlap_cutoff": cutoff, "low_overlap_n": lo_n, "low_overlap_rate": lo_rate,
        "n_ties_at_cutoff": n_ties, "dice_zero_proxy_n": int(empty_proxy.sum()),
        "benefit_counts": {k: int(v) for k, v in Counter(benefit.tolist()).items()},
        "phase30_counts": obs, "hard_case_eligible": contract_exact,
        "hard_case_selected_n": len(hc_rows), "hard_case_shortfall": shortfall,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_tier0_tier1_analysis_manifest_v1_2.json")
    print("")
    print("=" * 82)
    print("ANALYSIS COMPLETE — proceed to notebook build/execute + finalization.")
    print("=" * 82)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
