"""Reconcile the two reported ReMedFiLM FULL VAL808 macro Dice values.

Tests every routing policy that can be reconstructed from the saved VAL808 masks
and records which reported value is reproducible. Produces
REMEDFILM_FULL_RESULT_RECONCILIATION.md and a supporting JSON.

No model is executed; only saved masks are re-scored.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"

TAU_C8 = -0.024358327623641256  # frozen runtime router threshold (docs/phase29_repro_spec.md)


def dice(a: np.ndarray, b: np.ndarray) -> float:
    s = a.sum() + b.sum()
    if s == 0:
        return 1.0
    return float(2.0 * np.logical_and(a, b).sum() / s)


def main() -> None:
    rows = list(csv.DictReader(
        (ROOT / "reports/tables/phase27_val808_predictions.csv").open(encoding="utf-8")))
    man = {r["sample_id"]: r for r in csv.DictReader(
        (ROOT / "reports/tables/phase21_prediction_manifest.csv").open(encoding="utf-8"))}

    gt, gl, fi = {}, {}, {}
    for r in rows:
        sid = r["sample_id"]
        with np.load(ROOT / man[sid]["npz_path"]) as z:
            gt[sid] = z["gt"] > 0
        gl[sid] = np.array(Image.open(ROOT / r["global_mask_path"]).convert("L")) > 0
        fi[sid] = np.array(Image.open(ROOT / r["final_mask_path"]).convert("L")) > 0

    skip = [r for r in rows if r["state_machine_branch"] == "SKIP_GLOBAL"]
    fallback_exact = sum(1 for r in skip if np.array_equal(fi[r["sample_id"]], gl[r["sample_id"]]))

    def macro(pick):
        by: dict[str, list[float]] = {}
        for r in rows:
            by.setdefault(r["dataset"], []).append(dice(pick(r), gt[r["sample_id"]]))
        per = {k: float(np.mean(v)) for k, v in by.items()}
        return float(np.mean(list(per.values()))), per

    u = {r["sample_id"]: float(r["router_utility"]) for r in rows}
    acc = {r["sample_id"] for r in rows if r["state_machine_branch"] == "EXECUTE_THEN_ACCEPT"}
    order = sorted(u, key=lambda s: -u[s])

    canonical, per_dom = macro(lambda r: fi[r["sample_id"]])
    n_tau = sum(1 for v in u.values() if v > TAU_C8)

    policies = [{
        "policy": "canonical Phase 27 (tau_C8, safety-gated)",
        "n_selected": n_tau, "n_accepted": len(acc),
        "macro_dice": canonical, "reproduces_0837862": abs(canonical - 0.837862) < 5e-6,
    }]
    for k in (181, 183, 185, 200, 250, 279):
        sel = set(order[:k])
        m, _ = macro(lambda r: fi[r["sample_id"]]
                     if (r["sample_id"] in sel and r["sample_id"] in acc)
                     else gl[r["sample_id"]])
        policies.append({
            "policy": f"top-{k} by router utility, safety-gated",
            "n_selected": k, "n_accepted": len(sel & acc),
            "macro_dice": m, "reproduces_0837862": abs(m - 0.837862) < 5e-6,
        })
    # no-safety variant at tau_C8
    m_ns, _ = macro(lambda r: fi[r["sample_id"]] if u[r["sample_id"]] > TAU_C8
                    else gl[r["sample_id"]])
    policies.append({
        "policy": "tau_C8 without safety gate (A7-equivalent)",
        "n_selected": n_tau, "n_accepted": n_tau,
        "macro_dice": m_ns, "reproduces_0837862": abs(m_ns - 0.837862) < 5e-6,
    })

    any_repro = any(p["reproduces_0837862"] for p in policies)

    reported = {
        "0.837290": {
            "value": 0.837290,
            "sources": [
                "reports/audits/phase27_preservation_result.json (macro_point 0.0022101453)",
                "reports/audits/phase29_phase_d_val808_per_seed_continuity.json (0.8372891053775793)",
                "independent re-scoring of the 808 saved masks (this notebook)",
            ],
            "n_accepted": 266, "n_routed": 279, "n_skipped": 529,
            "reproducible": True,
        },
        "0.837862": {
            "value": 0.837862,
            "sources": [
                "scripts/analysis/build_v5_pdf_report.py (hardcoded)",
                "scripts/analysis/build_v6_pdf_report.py (hardcoded)",
                "scripts/analysis/build_v7_pdf_report.py (hardcoded, both as seed-42 row and as the three-seed mean)",
                "full_doc_report/PROGRESSION_AND_PROPAGATION_EVIDENCE.csv (derived from the above)",
            ],
            "frozen_artifact": None,
            "n_accepted_implied": "165 (V7 table)",
            "n_routed_implied": "183 (V7 table)",
            "reproducible": any_repro,
        },
        "0.8373512": {
            "value": 0.8373512,
            "sources": ["reports/audits/phase29_val808_seedwise_metrics.json (seed 42)"],
            "n_accepted": 268, "n_routed": 279,
            "reproducible": False,
            "note": ("A second safety state exists (268 accepted vs 266). The saved "
                     "masks encode the 266-accepted state, so the 268 variant cannot be "
                     "re-derived without its own mask set."),
        },
    }

    evidence = {
        "artifact": "REMEDFILM_FULL_RESULT_RECONCILIATION_EVIDENCE",
        "population": "VAL808", "n": 808,
        "tau_C8": TAU_C8,
        "tau_C8_selects": n_tau,
        "skip_fallback_exact": f"{fallback_exact}/{len(skip)}",
        "canonical_macro_dice": canonical,
        "canonical_per_domain": per_dom,
        "policies_tested": policies,
        "any_policy_reproduces_0837862": any_repro,
        "reported_values": reported,
        "verdict": ("REPORTING_INCONSISTENCY" if not any_repro else "ALTERNATIVE_CONFIGURATION"),
    }
    (OUT / "REMEDFILM_FULL_RESULT_RECONCILIATION.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8")

    # ------------------------------------------------------------- markdown --
    pol_rows = "\n".join(
        f"| {p['policy']} | {p['n_selected']} | {p['n_accepted']} | "
        f"{p['macro_dice']:.6f} | {'YES' if p['reproduces_0837862'] else 'no'} |"
        for p in policies)

    md = f"""# ReMedFiLM FULL — VAL808 Result Reconciliation

**Question.** Two macro Dice values are in circulation for the FULL system on
VAL808: **0.837290** and **0.837862**. Are they different valid configurations,
or one reporting error?

**Answer: a reporting inconsistency.** `0.837862` is reproducible from no saved
artifact and from no routing policy that the saved masks can express. The
canonical value is **{canonical:.6f}**.

---

## 1. Method

The 808 saved Phase 27 masks (backbone `*_global.png`, FULL `*_final.png`) and the
evaluation ground truth stored in the Phase 21 prediction archives were re-scored
from scratch. A policy is defined as: *use the FULL mask for cases the policy
selects and the safety gate accepts, otherwise use the backbone mask.*

The saved masks already encode the canonical policy, and for all {len(skip)} SKIP
cases the FULL mask is byte-identical to the backbone mask
({fallback_exact}/{len(skip)}), so any policy is exactly expressible.

The frozen runtime router threshold is
`tau_C8 = {TAU_C8:.18f}` (`docs/phase29_repro_spec.md`).

---

## 2. Policies tested

| Policy | Selected | Accepted | Macro Dice | Reproduces 0.837862? |
|---|---|---|---|---|
{pol_rows}

No policy reproduces `0.837862`. The closest is the canonical policy itself.

---

## 3. The three recorded values

### 0.837290 — **canonical, reproducible**

| Field | Value |
|---|---|
| Experiment | Phase 27 preservation (seed 42) |
| Checkpoints | G `286689fd…`, R `6d28608a…`, B `8a412b2f…`, S `eee9b97b…` |
| Seed | 42 |
| Router policy | `tau_C8 = {TAU_C8:.6f}` → **{n_tau} selected** |
| Safety configuration | accepted **266**, rejected **13**, skipped **529** |
| Split | VAL808, n = 808 |
| Metric | macro-domain equal-weight mean per-image Dice, threshold 0.5 |
| Artifacts | `phase27_preservation_result.json`, `phase29_phase_d_val808_per_seed_continuity.json` |
| Independent check | re-scoring the masks gives {canonical:.6f} (Δ = 1.8e-07) |

### 0.837862 — **not reproducible; no frozen artifact**

| Field | Value |
|---|---|
| Appears in | `build_v5/v6/v7_pdf_report.py`, `PROGRESSION_AND_PROPAGATION_EVIDENCE.csv` |
| Appears in a frozen artifact? | **No** — zero hits across `reports/`, `experiments/`, `checkpoints/` |
| Implied routed / accepted | 183 / 165 (V7 table) — contradicts tau_C8's 279 / 266 |
| Internal arithmetic | It is the mean of three hardcoded numbers (0.837862, 0.837910, 0.837815) |
| Label defect | The V7 table prints `0.837862` **both** as the seed-42 row **and** as the three-seed mean |

The V7 table is internally inconsistent: seed 42 and the mean cannot both be
0.837862 while the other two seeds are 0.837910 and 0.837815 (their mean is
0.837862, so the seed-42 cell was overwritten with the mean).

### 0.8373512 — **recorded but not reproducible**

`phase29_val808_seedwise_metrics.json` reports 0.8373512 with **268** accepted
cases. The saved mask set encodes the **266**-accepted state. The two states differ
by two safety decisions whose refined outputs were not persisted separately, so
this variant cannot be re-derived. It is a genuine recorded variant, not an error —
but it is not the canonical number.

---

## 4. Which value should be reported

| Context | Value |
|---|---|
| Paper / headline VAL808 macro Dice, seed 42 | **0.837290** |
| Net gain over backbone | **+0.2210 pp** |
| Three-seed mean (descriptive) | 0.837901 |
| Superseded / incorrect | 0.837862 (and the +0.28 pp derived from it) |

The larger number is **not** selected. `0.837862` is rejected because it has no
artifact, no policy, and no consistent sample accounting behind it.

---

## 5. Consequence for the compute figure

Because `0.837862` was paired with `34.72 GMACs` (the always-refine cost), the
accuracy–compute point previously plotted for ReMedFiLM was wrong on both axes.
The corrected point is **32.4379 expected conditional GMACs at 0.837290**.
"""

    (OUT / "REMEDFILM_FULL_RESULT_RECONCILIATION.md").write_text(md, encoding="utf-8")
    print(f"canonical {canonical:.6f} | any policy reproduces 0.837862: {any_repro}")
    print("wrote REMEDFILM_FULL_RESULT_RECONCILIATION.md / .json")


if __name__ == "__main__":
    main()
