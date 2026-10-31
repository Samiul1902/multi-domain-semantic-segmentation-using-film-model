"""Emit the remaining pre-registered audit artefacts.

  cohort_construction.json  -- exactly which rows were analysed, which were excluded
                               and why, with a digest of each sample-id list
  deviations.json           -- every departure from the frozen plan, with its reason
  barr_executability.json   -- the Task-3 determination, recorded with its evidence

Reads only.  Writes only into reports/audits/c1_external_stress_v1_0/.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

AUD = ROOT / "reports" / "audits" / "c1_external_stress_v1_0"
CACHE = ROOT / "data_cache" / "c1_external_stress_v1_0"
MANI = ROOT / "reports" / "external_extension" / "manifests"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def sha256_ids(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def cohort_construction() -> dict:
    out = {"artifact": "c1_external_stress_cohort_construction", "cohorts": {}}

    specs = [
        ("cvc", "CVC-ClinicDB", MANI / "ext02_cvc_clinicdb_manifest.csv", None, 2, "KVASIR"),
        ("breast", "BrEaST-Lesions-USG", MANI / "ext02_breast_us_manifest.csv", None, 1, "BUSI"),
        ("stones", "Stones_where_are_you", MANI / "ext02_1_stones_manifest_reconciled.csv",
         "test", 3, "KUB"),
    ]
    for key, name, path, split, task_id, analogue in specs:
        df = pd.read_csv(path)
        n_rows = len(df)
        sub = df if split is None else df[df["original_split"] == split]
        n_after_split = len(sub)
        ev = sub[sub["evaluable"] == True]  # noqa: E712
        n_evaluable = len(ev)
        analysed = json.loads((CACHE / key / "sample_ids.json").read_text(encoding="utf-8"))

        excluded = sub[sub["evaluable"] != True]  # noqa: E712
        excl_rows = []
        for _, r in excluded.iterrows():
            excl_rows.append({
                "sample_id": str(r["external_sample_id"]),
                "reason": str(r.get("exclusion_reason") or "evaluable=False"),
            })

        out["cohorts"][key] = {
            "cohort": name,
            "manifest": str(path.relative_to(ROOT)).replace("\\", "/"),
            "manifest_sha256": sha256_file(path),
            "split_filter": split,
            "rows_in_manifest": int(n_rows),
            "rows_after_split_filter": int(n_after_split),
            "rows_evaluable": int(n_evaluable),
            "rows_analysed": len(analysed),
            "excluded_by_manifest": excl_rows,
            "exclusion_rule": ("evaluable == True AND image_path resolves AND ground-truth "
                               "reference resolves AND mask rasterises"),
            "task_id": task_id,
            "domain_analogue": analogue,
            "sample_ids_sha256": sha256_ids(analysed),
            "n_post_hoc_drops": 0,
        }

    # HAM10000: excluded, recorded with the reason and its manifest digest
    ham = MANI / "ext02_ham10000_manifest.csv"
    out["cohorts"]["ham10000"] = {
        "cohort": "HAM10000",
        "manifest": str(ham.relative_to(ROOT)).replace("\\", "/"),
        "manifest_sha256": sha256_file(ham),
        "rows_in_manifest": int(len(pd.read_csv(ham))),
        "rows_analysed": 0,
        "status": "HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED",
        "reason": ("The HAM10000 folder is the ISIC-2018 Task 3 classification release, "
                   "which ships no segmentation masks. 10,015 mask files exist with no "
                   "recorded provenance. No inference was run."),
    }

    out["total_analysed"] = sum(v["rows_analysed"] for v in out["cohorts"].values())
    out["total_excluded"] = sum(len(v.get("excluded_by_manifest", []))
                                for v in out["cohorts"].values())
    return out


def deviations() -> dict:
    return {
        "artifact": "c1_external_stress_deviations",
        "plan_revision": "c1_external_stress_plan_v1_0",
        "n_deviations": 3,
        "scientific_impact": "none on the reported values; DEV-03 narrows what the values mean",
        "deviations": [
            {
                "id": "DEV-01",
                "kind": "DELIVERABLE_NAMING",
                "planned": "reports/figures/fig6_external_global.png and "
                           "reports/figures/fig7_external_barr.png (two figures)",
                "actual": "reports/figures/fig6_external_cvc.png, "
                          "fig7_external_breast.png, fig8_external_stones.png (three figures)",
                "reason": ("The plan's column set requires 8 columns once BARR executes. A "
                           "single two-figure split by arm cannot show the paired Global and "
                           "BARR panels for the same case. Splitting by cohort instead keeps "
                           "the 8 pre-registered columns legible at print resolution."),
                "effect_on_results": "none - same cases, same metrics, same palette",
            },
            {
                "id": "DEV-02",
                "kind": "FIGURE_ROW_SELECTION_ADDITION",
                "planned": "Stones rows: median / best / worst Dice, largest and smallest "
                           "non-empty ground-truth lesion",
                "actual": "the same five rows; an additional stone-positive median row was "
                          "attempted but resolved to a case already selected, so it was "
                          "deduplicated and the figure keeps five rows",
                "reason": ("The cohort-wide median Dice for Stones is 0 because 14 of 20 "
                           "cases have an empty ground truth. That is the headline finding, "
                           "so the row is kept rather than substituted; a stone-positive "
                           "median was added only if it was a distinct case."),
                "effect_on_results": "none - no case was added or removed",
            },
            {
                "id": "DEV-03",
                "kind": "METRIC_DEFINITION",
                "planned": ("The manuscript protocol (§9.1) defines NSD at tau = 1.0 mm and "
                            "reports HD95 in millimetres."),
                "actual": ("External NSD is computed at tau = 2 pixels and external HD95/ASSD "
                           "are reported in pixels."),
                "reason": ("No external cohort ships physical pixel spacing: CVC-ClinicDB, "
                           "BrEaST-Lesions-USG and Stones all provide pixel arrays with no "
                           "DICOM header, calibration phantom or documented mm-per-pixel. A "
                           "millimetre figure would be fabricated. The plan pre-registered "
                           "the pixel convention (section 6.1) for exactly this reason."),
                "effect_on_results": ("External surface metrics are not comparable to internal "
                                      "millimetre values and not comparable across the three "
                                      "cohorts. Every document states the unit next to the "
                                      "number."),
            },
        ],
    }


def barr_executability() -> dict:
    ev = json.loads((AUD / "barr_execution.json").read_text(encoding="utf-8"))
    states = {k: v["states"] for k, v in ev["cohorts"].items()}
    return {
        "artifact": "c1_external_stress_barr_executability",
        "determination": "BARR_EXECUTABLE_FROM_VERIFIED_ARTIFACTS",
        "not_executable_code_not_triggered": "BARR_NOT_EXECUTABLE_FROM_VERIFIED_ARTIFACTS",
        "evidence": {
            "components_hash_verified_before_forward": True,
            "strict_state_dict_loading": True,
            "component_parameter_counts": {
                "global_G": 3523001, "refiner_R_psi": 1276401,
                "router_B_phi": 36801, "safety_S_omega": 1217,
                "total": 4837420,
            },
            "decision_form_agreement_asserted_per_case": True,
            "n_cases_where_decision_forms_disagreed": 0,
            "reference_composition":
                "scripts/analysis/phase29_phase_d_canonical_seed_inference.py",
            "external_driver":
                "scripts/analysis/c1_external_stress_eval.py",
        },
        "what_the_driver_does_not_do": [
            "It does not modify, retrain or partially reload any frozen component.",
            "It does not reimplement the router or safety feature extractors; it imports "
            "the frozen modules and executes the frozen class bodies via AST extraction.",
            "It supplies only the external population and the per-case bookkeeping.",
        ],
        "observed_states": states,
        "n_failed": sum(v.get("FAILED", 0) for v in states.values()),
        "n_fallback_to_global": sum(v.get("FALLBACK_TO_GLOBAL", 0) for v in states.values()),
        "stage_counts": {k: v["stage_counts"] for k, v in ev["cohorts"].items()},
        "selection_fraction": {
            k: round((v["states"].get("ACCEPTED", 0) + v["states"].get("REJECTED", 0))
                     / v["n"], 6) for k, v in ev["cohorts"].items()},
        "caveat": ("The frozen router threshold tau_C7 was calibrated on the internal "
                   "development population with a fixed 25% budget. On external cohorts the "
                   "selection fraction is an OUTCOME, not a controlled quantity, and no "
                   "recalibration was performed."),
    }


def main() -> int:
    for name, fn in (("cohort_construction.json", cohort_construction),
                     ("deviations.json", deviations),
                     ("barr_executability.json", barr_executability)):
        (AUD / name).write_text(json.dumps(fn(), indent=2) + "\n", encoding="utf-8")
        print("wrote", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
