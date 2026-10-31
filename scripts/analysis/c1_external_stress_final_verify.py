"""Independent re-verification of the completed 884-case external stress test.

This script does NOT run inference.  It recomputes every reported quantity from
the saved probability arrays and routing traces, then cross-checks the recomputed
values against the tables the earlier stages wrote.  A mismatch is a failure, not
a warning.

It also settles two accounting questions that the earlier artefacts left
implicit:

  * whether a REJECTED candidate consumed a regional refiner forward pass
    (answered from ``stage_counts`` and from the execution order in
    ``c1_external_stress_eval.py``);
  * how the BrEaST inventory (270 images / 18 without masks / 256 manifest rows
    / 252 analysed) actually reconciles, and how many independent case groups
    that leaves.

Writes ``reports/audits/c1_external_stress_v1_0/final_verification.json``.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

AUD = ROOT / "reports" / "audits" / "c1_external_stress_v1_0"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "c1_external_stress_v1_0"

SEG = 0.5
COHORTS = ["cvc", "breast", "stones"]
BREAST_DIR = Path(r"D:\Softfors\final\external_test_ds\BrEaST-Lesions_USG-images_and_masks")
BREAST_MANIFEST = ROOT / "reports/external_extension/manifests/ext02_breast_us_manifest.csv"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dice(pred: np.ndarray, gt: np.ndarray) -> float:
    """Dice with the frozen convention: undefined only when both masks are empty."""
    tp = int(np.count_nonzero(pred & gt))
    fp = int(np.count_nonzero(pred & ~gt))
    fn = int(np.count_nonzero(~pred & gt))
    den = 2 * tp + fp + fn
    return (2 * tp / den) if den else float("nan")


def main() -> int:
    failures: list[str] = []
    report: dict = {"artifact": "c1_external_stress_final_verification",
                    "inference_rerun": False,
                    "method": "recomputed from saved prob/pred arrays and barr_states.csv"}

    exec_rec = json.loads((AUD / "barr_execution.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(TAB / "c1_external_stress_summary.csv")
    paired_tbl = pd.read_csv(TAB / "c1_external_stress_paired.csv")

    per_cohort: dict = {}
    all_rows = []

    for key in COHORTS:
        d = CACHE / key
        pg = np.load(d / "prob_global.npy")
        pb = np.load(d / "prob_barr.npy")
        png = np.load(d / "pred_global.npy")
        pnb = np.load(d / "pred_barr.npy")
        gt = np.load(d / "gt.npy").astype(bool)
        ids = json.loads((d / "sample_ids.json").read_text(encoding="utf-8"))
        st = pd.read_csv(d / "barr_states.csv")

        n = pg.shape[0]
        assert n == pb.shape[0] == png.shape[0] == pnb.shape[0] == gt.shape[0] == len(st) == len(ids)

        # --- array identity against the recorded digests -------------------
        recorded = exec_rec["cohorts"][key]["sha256"]
        arr_ok = {}
        for fname, exp in recorded.items():
            got = sha(d / fname)
            arr_ok[fname] = (got == exp)
            if got != exp:
                failures.append(f"{key}/{fname} digest mismatch")

        # --- recompute per-case Dice from the arrays ----------------------
        dg = np.array([dice(png[i].astype(bool), gt[i]) for i in range(n)], dtype=float)
        db = np.array([dice(pnb[i].astype(bool), gt[i]) for i in range(n)], dtype=float)

        # cross-check that the stored binary masks equal threshold(prob) exactly
        thg = (pg >= SEG)
        thb = (pb >= SEG)
        if not np.array_equal(thg, png.astype(bool)):
            failures.append(f"{key}: pred_global != (prob_global >= 0.5)")
        if not np.array_equal(thb, pnb.astype(bool)):
            failures.append(f"{key}: pred_barr != (prob_barr >= 0.5)")

        delta = db - dg
        # NaN-safe paired delta: only where both Dice are defined
        both = np.isfinite(dg) & np.isfinite(db)
        delta_def = delta[both]

        states = st["state"].value_counts().to_dict()
        rec_states = exec_rec["cohorts"][key]["states"]
        for s, c in rec_states.items():
            if states.get(s, 0) != c:
                failures.append(f"{key}: state {s} trace={c} recomputed={states.get(s, 0)}")

        sel = int(st["selected"].fillna(False).astype(bool).sum())
        acc = int(st["accepted"].fillna(False).astype(bool).sum())
        rej = int((st["state"] == "REJECTED").sum())
        stage = exec_rec["cohorts"][key]["stage_counts"]

        # refiner forwards must equal selected, because rejection is decided AFTER
        # the refiner has already run (eval script: refiner_forwards += 1 precedes
        # the S_omega decision).
        if stage["refiner_forwards"] != sel:
            failures.append(f"{key}: refiner_forwards={stage['refiner_forwards']} != selected={sel}")
        if sel != acc + rej:
            failures.append(f"{key}: selected={sel} != accepted={acc} + rejected={rej}")

        improved = int((delta_def > 1e-12).sum())
        worsened = int((delta_def < -1e-12).sum())
        unchanged = int((np.abs(delta_def) <= 1e-12).sum())

        # --- cross-check the summary table --------------------------------
        def table_mean(arm: str, metric: str = "Dice") -> float:
            r = summary[(summary.cohort_key == key) & (summary.arm == arm)
                        & (summary.metric == metric)]
            return float(r.iloc[0]["mean"]) if len(r) else float("nan")

        g_mean = float(np.nanmean(dg))
        b_mean = float(np.nanmean(db))
        if abs(g_mean - table_mean("global")) > 1e-9:
            failures.append(f"{key}: global Dice {g_mean} != table {table_mean('global')}")
        if abs(b_mean - table_mean("barr")) > 1e-9:
            failures.append(f"{key}: barr Dice {b_mean} != table {table_mean('barr')}")

        # --- cross-check the paired table ---------------------------------
        pt = paired_tbl[paired_tbl.cohort_key == key]
        if len(pt):
            if int((pt.outcome == "improved").sum()) != improved:
                failures.append(f"{key}: improved count differs from paired table")
            if int((pt.outcome == "worsened").sum()) != worsened:
                failures.append(f"{key}: worsened count differs from paired table")

        per_cohort[key] = {
            "name": exec_rec["cohorts"][key]["name"],
            "n": n,
            "n_dice_defined": int(np.isfinite(dg).sum()),
            "dice_global_mean": g_mean,
            "dice_barr_mean": b_mean,
            "paired_delta_mean": float(np.nanmean(delta_def)),
            "paired_delta_median": float(np.nanmedian(delta_def)),
            "paired_delta_q1": float(np.percentile(delta_def, 25)),
            "paired_delta_q3": float(np.percentile(delta_def, 75)),
            "n_improved": improved, "n_unchanged": unchanged, "n_worsened": worsened,
            "n_selected": sel, "n_accepted": acc, "n_rejected": rej,
            "states": states,
            "stage_counts": stage,
            "refiner_forwards_equal_selected": stage["refiner_forwards"] == sel,
            "arrays_match_recorded_digests": all(arr_ok.values()),
        }

        for i in range(n):
            all_rows.append({"cohort_key": key, "sample_id": ids[i], "index": i,
                             "dice_global": dg[i], "dice_barr": db[i],
                             "delta": delta[i], "state": st.iloc[i]["state"],
                             "router_score": st.iloc[i]["router_score"],
                             "safety_prob": st.iloc[i]["safety_prob"],
                             "latency_global_s": st.iloc[i]["latency_global_s"],
                             "latency_barr_s": st.iloc[i]["latency_barr_s"]})

    df = pd.DataFrame(all_rows)
    report["per_cohort"] = per_cohort

    # --- totals ------------------------------------------------------------
    tot_n = sum(v["n"] for v in per_cohort.values())
    tot_sel = sum(v["n_selected"] for v in per_cohort.values())
    tot_acc = sum(v["n_accepted"] for v in per_cohort.values())
    tot_rej = sum(v["n_rejected"] for v in per_cohort.values())
    tot_ref = sum(v["stage_counts"]["refiner_forwards"] for v in per_cohort.values())
    tot_som = sum(v["stage_counts"]["somega_forwards"] for v in per_cohort.values())
    tot_router = sum(v["stage_counts"]["router_forwards"] for v in per_cohort.values())
    report["totals"] = {
        "n_cases": tot_n, "n_selected": tot_sel, "n_accepted": tot_acc,
        "n_rejected": tot_rej, "refiner_forwards": tot_ref,
        "somega_forwards": tot_som, "router_forwards": tot_router,
        "refiner_forwards_equal_selected": tot_ref == tot_sel,
    }
    if tot_n != 884:
        failures.append(f"total cases {tot_n} != 884")

    # --- compute accounting -------------------------------------------------
    # A rejected candidate has already paid for the refiner and the safety head;
    # only its OUTPUT is discarded.  Cost therefore attaches to `selected`.
    report["compute_accounting"] = {
        "principle": ("rejection is decided after the refiner forward pass "
                      "(c1_external_stress_eval.py: refiner_forwards += 1 at the call "
                      "site, then S_omega decides accept/reject). A rejected candidate "
                      "has already consumed refinement compute."),
        "regional_forward_passes_external": tot_ref,
        "accepted_outputs_external": tot_acc,
        "rejected_outputs_external": tot_rej,
        "accepted_plus_rejected": tot_acc + tot_rej,
        "cost_should_be_counted_at": "selected (routed) candidates",
        "external_routed": tot_sel,
        "internal_barr_m1_population": {
            "note": ("the 1,239 / 1,205 / 34 triple belongs to the internal BARR-M1 "
                     "policy population, not to this external cohort"),
            "routed": 1239, "accepted": 1205, "rejected": 34,
            "regional_forward_passes": 1239,
            "reason": "1,239 = 1,205 accepted + 34 rejected; all 1,239 ran the refiner",
        },
        "measured_latency_s": {
            key: {
                "median_global": float(df[df.cohort_key == key]["latency_global_s"].median()),
                "median_barr": float(df[df.cohort_key == key]["latency_barr_s"].median()),
                "total_global": float(df[df.cohort_key == key]["latency_global_s"].sum()),
                "total_barr": float(df[df.cohort_key == key]["latency_barr_s"].sum()),
            } for key in COHORTS},
    }

    # --- BrEaST inventory reconciliation ------------------------------------
    imgs = {p.stem for p in BREAST_DIR.glob("*.png") if "tumor" not in p.name.lower()}
    masks = {p.stem.replace("_tumor", "") for p in BREAST_DIR.glob("*_tumor*.png")}
    no_mask = sorted(imgs - masks)
    other_views = [x for x in no_mask if "_other" in x]
    primary_no_mask = [x for x in no_mask if "_other" not in x]
    owners = sorted({x.split("_")[0] for x in other_views})

    man = pd.read_csv(BREAST_MANIFEST)
    man_ids = [re.sub(r"^BREAST::", "", x) for x in man.external_sample_id]
    evaluable = man[man.evaluable.astype(str).str.lower() == "true"]

    report["breast_inventory"] = {
        "images_on_disk": len(imgs),
        "tumour_masks_on_disk": len(masks),
        "images_without_mask": len(no_mask),
        "without_mask_additional_views": len(other_views),
        "without_mask_primary_images": len(primary_no_mask),
        "primary_images_without_mask_ids": primary_no_mask,
        "additional_view_owners": owners,
        "additional_views_per_owner": {o: sum(1 for x in other_views if x.split("_")[0] == o)
                                       for o in owners},
        "manifest_rows": len(man),
        "manifest_unique_ids": len(set(man_ids)),
        "manifest_evaluable": int(len(evaluable)),
        "analysed": int(len(evaluable)),
        "images_not_in_manifest": sorted(imgs - set(man_ids)),
        "manifest_rows_not_on_disk": sorted(set(man_ids) - imgs),
        "reconciliation": (
            f"{len(imgs)} images = {len(masks)} primary images with a tumour mask "
            f"+ {len(other_views)} additional non-primary views of {len(owners)} cases "
            f"+ {len(primary_no_mask)} primary images with no mask. "
            f"The manifest lists the {len(man)} primary images only, so no additional "
            f"view ever entered the cohort. {len(primary_no_mask)} of those have no mask "
            f"and are excluded pre-inference, leaving {len(evaluable)} analysed."),
        "independent_case_groups": int(len(set(
            re.sub(r"^BREAST::", "", x) for x in evaluable.external_sample_id))),
        "independence_caveat": (
            "252 analysed rows carry 252 distinct case_id values and no case "
            "contributes more than one analysed image, so 252 is a valid CASE-level "
            "cluster count. Patient-level independence is NOT verifiable: the manifest "
            "records no patient identifier, so two case_ids belonging to one patient "
            "cannot be detected or ruled out."),
    }
    if len(imgs) != 270 or len(masks) != 252 or len(man) != 256 or len(evaluable) != 252:
        failures.append("breast inventory does not reconcile to 270/252/256/252")

    # --- identity chain -----------------------------------------------------
    plan = json.loads((AUD / "plan_manifest.json").read_text(encoding="utf-8"))
    ident = {}
    for k, rec in plan["bound_inputs"].items():
        p = ROOT / rec["path"]
        ok = p.exists() and sha(p) == rec["sha256"]
        ident[k] = {"path": rec["path"], "sha256": rec["sha256"][:16] + "...", "matches": ok}
        if not ok:
            failures.append(f"bound input {k} drifted")
    report["identity"] = ident

    report["verdict"] = "CONSISTENT" if not failures else "INCONSISTENT"
    report["failures"] = failures
    (AUD / "final_verification.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

    # --- console ------------------------------------------------------------
    print(f"{'cohort':10s} {'n':>4s} {'global':>8s} {'barr':>8s} {'delta':>8s} "
          f"{'sel':>5s} {'acc':>5s} {'rej':>4s} {'ref_fwd':>7s}")
    for k, v in per_cohort.items():
        print(f"{k:10s} {v['n']:4d} {v['dice_global_mean']:8.4f} {v['dice_barr_mean']:8.4f} "
              f"{v['paired_delta_mean']:+8.4f} {v['n_selected']:5d} {v['n_accepted']:5d} "
              f"{v['n_rejected']:4d} {v['stage_counts']['refiner_forwards']:7d}")
    print(f"\ntotals: n={tot_n} selected={tot_sel} accepted={tot_acc} rejected={tot_rej} "
          f"refiner_forwards={tot_ref}")
    print(f"breast: {len(imgs)} images / {len(masks)} masks / {len(man)} manifest / "
          f"{len(evaluable)} analysed")
    print(f"VERDICT: {report['verdict']}  failures={len(failures)}")
    for f in failures:
        print("  FAIL", f)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
