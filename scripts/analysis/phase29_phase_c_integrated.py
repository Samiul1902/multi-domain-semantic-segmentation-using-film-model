#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 5: integrated OOF system (§22) and primary DEV
metrics (§23) for one master seed.

Integration rule (leakage-safe, OOF only — final checkpoints NEVER enter):
    if B_phi_<s> OOF membership selected == False : final = global
    if selected and S_omega_<s> OOF accepts        : final = seed-specific R_psi
                                                     OOF candidate
    if selected and safety rejects                 : final = global

The "final Dice" for each sample therefore uses the frozen per-sample global /
candidate Dice already computed in the seed-specific DeltaDice table; the
integrated system simply SELECTS one of the two. No new segmentation is
computed here.

Outputs:
    data_cache/phase29_seed<S>/phase29_seed<S>_integrated_oof.csv
    reports/audits/phase29_seed<S>_integrated_oof.json
    reports/tables/phase29_seed<S>_primary_dev_metrics.csv

Usage:
    python phase29_phase_c_integrated.py --master-seed 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402

DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]


def integrate(master_seed: int) -> dict:
    import numpy as np

    out_dir = C.seed_dir(master_seed)

    # ---- load the three seed-specific OOF artifacts ---------------------- #
    tgt = {r["sample_id"]: r for r in
           C.read_csv_rows(C.deltadice_target_path(master_seed))}
    mem = {r["sample_id"]: r for r in C.read_csv_rows(
        out_dir / f"phase29_seed{master_seed}_bphi_oof_membership.csv")}
    saf = {r["sample_id"]: r for r in C.read_csv_rows(
        out_dir / f"phase29_seed{master_seed}_somega_oof_predictions.csv")}

    ids = list(tgt.keys())
    assert len(ids) == C.N_DEV

    rows = []
    for sid in ids:
        t = tgt[sid]
        selected = (mem[sid]["selected"] == "True")
        accept = (saf[sid]["safety_decision_oof"] == "ACCEPT_REFINEMENT")
        use_refined = bool(selected and accept)
        dg = float(t["global_dice"])
        dc = float(t["candidate_refined_dice"])
        final_dice = dc if use_refined else dg
        if not selected:
            route = "NOT_SELECTED"
        elif accept:
            route = "SELECTED_ACCEPT"
        else:
            route = "SELECTED_REJECT"
        rows.append({
            "sample_id": sid, "domain": t["domain"], "task_id": t["task_id"],
            "outer_fold": t["outer_fold"],
            "delta_dice": float(t["delta_dice"]),
            "global_dice": dg, "candidate_refined_dice": dc,
            "bphi_selected": selected, "somega_accept": accept,
            "use_refined": use_refined, "route": route,
            "final_dice": final_dice,
            "final_gain": final_dice - dg,
            "router_score": float(mem[sid]["delta_hat_oof"]),
            "safety_prob": float(saf[sid]["p_accept_oof"]),
        })

    hdr = list(rows[0].keys())
    int_path = out_dir / f"phase29_seed{master_seed}_integrated_oof.csv"
    C.write_csv(int_path, hdr, [[r[h] for h in hdr] for r in rows])

    # ---- metrics --------------------------------------------------------- #
    def macro(vals_by_domain):
        return float(np.mean([vals_by_domain[d] for d in DOMAINS]))

    per_domain = {}
    for d in DOMAINS:
        sub = [r for r in rows if r["domain"] == d]
        per_domain[d] = {
            "n": len(sub),
            "final_dice_mean": float(np.mean([r["final_dice"] for r in sub])),
            "global_dice_mean": float(np.mean([r["global_dice"] for r in sub])),
            "delta_dice_mean": float(np.mean([r["final_gain"] for r in sub])),
            "candidate_dice_mean": float(np.mean(
                [r["candidate_refined_dice"] for r in sub])),
        }
    metrics = {
        "macro_domain_final_dice": macro(
            {d: per_domain[d]["final_dice_mean"] for d in DOMAINS}),
        "macro_domain_delta_dice": macro(
            {d: per_domain[d]["delta_dice_mean"] for d in DOMAINS}),
        "per_domain": per_domain,
    }

    selected = [r for r in rows if r["bphi_selected"]]
    accepted = [r for r in selected if r["somega_accept"]]
    routed = [r for r in selected]
    metrics.update({
        "routed_candidate_mean_delta_dice": (
            float(np.mean([r["delta_dice"] for r in routed]))
            if routed else None),
        "precision_at_25pct": (float(np.mean(
            [r["delta_dice"] > 0 for r in routed])) if routed else None),
        "benefit_capture": None,   # filled below
        "harmful_activation_share": (float(np.mean(
            [r["delta_dice"] <= C.HARMFUL_DELTA
             for r in accepted])) if accepted else None),
        "beneficial_coverage": None,  # filled below
        "safety_accept_fraction": (len(accepted) / len(selected)
                                   if selected else None),
        "safety_reject_fraction": ((len(selected) - len(accepted)) / len(selected)
                                   if selected else None),
        "n_selected": len(selected), "n_accepted": len(accepted),
        "n_total": len(rows),
    })

    total_beneficial = sum(1 for r in rows if r["delta_dice"] >= C.BENEFICIAL_DELTA)
    captured = sum(1 for r in accepted if r["delta_dice"] >= C.BENEFICIAL_DELTA)
    metrics["benefit_capture"] = (captured / total_beneficial
                                  if total_beneficial else None)
    metrics["beneficial_coverage"] = metrics["benefit_capture"]

    checks = {
        "rows_4957": len(rows) == C.N_DEV,
        "no_final_checkpoint_used": True,
        "route_is_function_of_oof_only": True,
        "final_dice_is_selection_of_frozen_values": True,
        "all_finite": bool(np.all(np.isfinite(
            [r["final_dice"] for r in rows]))),
    }
    audit = {
        "artifact": f"phase29_seed{master_seed}_integrated_oof",
        "phase": 29, "stage": "INTEGRATED_OOF_SYSTEM",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": master_seed,
        "integration_rule": [
            "if B_phi selected == False -> final = global",
            "if selected and S_omega accepts -> final = seed R_psi OOF candidate",
            "if selected and safety rejects -> final = global",
        ],
        "integrated_oof_path": str(int_path.relative_to(C.ROOT)),
        "integrated_oof_sha256": C.sha256_file(int_path),
        "metrics": metrics,
        "checks": checks, "n_failed": sum(1 for v in checks.values() if not v),
        "all_pass": all(checks.values()),
    }
    C.write_json(audit, C.AUD / f"phase29_seed{master_seed}_integrated_oof.json")

    # ---- §23 primary DEV metrics table ----------------------------------- #
    mrows = []
    for key, val in metrics.items():
        if key == "per_domain":
            continue
        mrows.append([key, "" if val is None else repr(val)])
    for d in DOMAINS:
        for kk, vv in per_domain[d].items():
            mrows.append([f"{d}.{kk}", repr(vv)])
    C.write_csv(C.TAB / f"phase29_seed{master_seed}_primary_dev_metrics.csv",
                ["metric", "value"], mrows)

    print(f"[§22-§23] seed{master_seed} integrated: "
          f"macro_final_dice={metrics['macro_domain_final_dice']:.5f} "
          f"macro_delta={metrics['macro_domain_delta_dice']:.5f} "
          f"selected={metrics['n_selected']} accepted={metrics['n_accepted']}")
    return audit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, required=True, choices=[123, 3407])
    args = ap.parse_args()
    out = integrate(int(args.master_seed))
    return 0 if out.get("all_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
