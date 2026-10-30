"""PHASE-13 PART-1B — §2 pre-repair evidence verification + §3 FIRST GATE.

Determines whether the PRIMARY checkpoint-selection evidence for epochs 1..28
is salvageable given the metric-semantics defect.

Logic (per supervisor §3):
  If EVERY epoch 1..28 emitted ZERO proposals, then the frozen primary coverage
  terms are invariant to the component-mask implementation bug, because with no
  proposals:
      tiny_recall90 = 0, overall_recall90 = 0, mean_roi_area_fraction = 0
  under EITHER the erroneous or the corrected component-mask evaluation.
  The only differentiating selection term is then -val_loss.

  -> PRE_REPAIR_PRIMARY_SELECTION_VALIDATED = TRUE

If ANY epoch shows proposals > 0 / nonzero primary recall / nonzero ROI
fraction / replay mismatch -> CHECK_REQUIRED, do not resume.

Read-only. No training. No model. No CUDA. No TEST.

Usage:
  python scripts/audits/gate_phase13_part1b_pre_repair_primary_selection.py
  python scripts/audits/gate_phase13_part1b_pre_repair_primary_selection.py --write-artifact
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
HISTORY = ROOT / "experiments" / EXP / "history.csv"
LATEST = ROOT / "checkpoints" / EXP / "latest.pt"
BEST = ROOT / "checkpoints" / EXP / "best.pt"
CONFIG = (
    ROOT / "configs" / "phase13_clean_v3"
    / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3.yaml"
)

OUT_JSON = (
    ROOT / "reports" / "audits"
    / "phase13_part1b_pre_repair_primary_selection_validation.json"
)
OUT_MD = (
    ROOT / "reports" / "audits"
    / "phase13_part1b_pre_repair_primary_selection_validation.md"
)

TOL = 1e-12

FROZEN_SHA = {
    "history.csv": (
        "70fca5b796d112b1322ae945570ec94a271f3502af0bac61664954a4b0d13031",
        HISTORY,
    ),
    "latest.pt": (
        "7f6f0b2e0d6fe2d61743ec0e3f8d2cf5e986f5711442cdf3113932da59152407",
        LATEST,
    ),
    "best.pt": (
        "d71aed3e084653bfc49acf9461cc2f0b3332c03b43026947a54393f89cebd04c",
        BEST,
    ),
    "config": (
        "922ff26916c1f7ebea0ea526fbaa6adbb9a7419f1f08b16d33ed5df049c4c8bf",
        CONFIG,
    ),
}

PRIMARY_ZERO_FIELDS = [
    "tiny_recall90",
    "overall_recall90",
    "mean_roi_area_fraction",
    "mean_proposals_per_image",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def verify_hashes() -> dict:
    result = {}
    for name, (expected, path) in FROZEN_SHA.items():
        actual = sha256_file(path) if path.exists() else "MISSING"
        result[name] = {
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
            "path": str(path),
        }
    return result


def gate_analysis() -> dict:
    with open(HISTORY, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    epochs = [int(r["epoch"]) for r in rows]
    contiguous = epochs == list(range(1, len(epochs) + 1))

    # ---- zero-proposal / zero-primary check per epoch ----
    offenders = []
    for row in rows:
        for field in PRIMARY_ZERO_FIELDS:
            value = float(row[field])
            if abs(value) > TOL:
                offenders.append(
                    {"epoch": int(row["epoch"]), "field": field, "value": value}
                )

    # ---- checkpoint epoch identity ----
    import torch

    latest_ck = torch.load(LATEST, map_location="cpu", weights_only=False)
    best_ck = torch.load(BEST, map_location="cpu", weights_only=False)
    latest_epoch = int(latest_ck.get("epoch", -1))
    best_epoch_ck = int(best_ck.get("epoch", -1))
    global_step = int(latest_ck.get("global_step", -1))

    # ---- independent replay of the frozen strict-lexicographic selection ----
    best_score = None
    replay_best_epoch = None
    replay_bad = 0
    replay_rows = []
    mismatches = []
    for row in rows:
        epoch = int(row["epoch"])
        score = (
            float(row["tiny_recall90"]),
            float(row["overall_recall90"]),
            -float(row["mean_roi_area_fraction"]),
            -float(row["val_loss"]),
        )
        if best_score is None or score > best_score:
            is_new_best = True
            best_score = score
            replay_best_epoch = epoch
            replay_bad = 0
        else:
            is_new_best = False
            replay_bad += 1

        rec_new = str(row["is_new_best"]).strip().lower() in {"true", "1"}
        rec_bad = int(float(row["bad_epochs"]))
        rec_best_so_far = int(float(row["best_epoch_so_far"]))

        if rec_new != is_new_best:
            mismatches.append(
                f"is_new_best@epoch{epoch}: recorded={rec_new} replayed={is_new_best}"
            )
        if rec_bad != replay_bad:
            mismatches.append(
                f"bad_epochs@epoch{epoch}: recorded={rec_bad} replayed={replay_bad}"
            )
        if rec_best_so_far != replay_best_epoch:
            mismatches.append(
                f"best_epoch_so_far@epoch{epoch}: recorded={rec_best_so_far} "
                f"replayed={replay_best_epoch}"
            )

        replay_rows.append(
            {
                "epoch": epoch,
                "score": list(score),
                "is_new_best": is_new_best,
                "best_epoch_so_far": replay_best_epoch,
                "bad_epochs": replay_bad,
            }
        )

    last = rows[-1]
    epoch28_bad = int(float(last["bad_epochs"]))
    epoch28_best_so_far = int(float(last["best_epoch_so_far"]))

    all_zero = len(offenders) == 0
    validated = (
        all_zero
        and contiguous
        and latest_epoch == 28
        and best_epoch_ck == 27
        and epoch28_bad == 1
        and epoch28_best_so_far == 27
        and replay_best_epoch == 27
        and not mismatches
    )

    return {
        "history_rows": len(rows),
        "epochs_contiguous_1_to_N": contiguous,
        "epochs_with_any_nonzero_primary": sorted({o["epoch"] for o in offenders}),
        "nonzero_primary_offenders": offenders,
        "all_epochs_zero_proposals": all_zero,
        "latest_pt_epoch": latest_epoch,
        "best_pt_epoch": best_epoch_ck,
        "persisted_global_step": global_step,
        "epoch28_bad_epochs": epoch28_bad,
        "epoch28_best_epoch_so_far": epoch28_best_so_far,
        "replayed_best_epoch": replay_best_epoch,
        "replayed_final_bad_epochs": replay_bad,
        "replayed_best_score": list(best_score) if best_score else None,
        "replay_mismatches": mismatches,
        "PRE_REPAIR_PRIMARY_SELECTION_VALIDATED": validated,
        "primary_validity_reason": (
            "ZERO_PROPOSALS_MAKES_COVERAGE_INVARIANT" if all_zero else "NOT_APPLICABLE"
        ),
    }


def main() -> int:
    hashes = verify_hashes()
    gate = gate_analysis()

    print("=" * 72)
    print("§2 PRE-STOP EVIDENCE VERIFICATION")
    print("=" * 72)
    for name, info in hashes.items():
        flag = "OK   " if info["match"] else "DRIFT"
        print(f"  {flag} {name:12s} {info['actual']}")
    hashes_ok = all(i["match"] for i in hashes.values())
    print(f"  ALL EVIDENCE UNCHANGED: {hashes_ok}")

    print()
    print("=" * 72)
    print("§3 FIRST GATE — PRE-REPAIR PRIMARY SELECTION SALVAGEABILITY")
    print("=" * 72)
    print(f"  history rows                     : {gate['history_rows']}")
    print(f"  epochs contiguous 1..N           : {gate['epochs_contiguous_1_to_N']}")
    print(f"  all epochs zero proposals        : {gate['all_epochs_zero_proposals']}")
    print(f"  epochs with nonzero primary      : {gate['epochs_with_any_nonzero_primary']}")
    print(f"  latest.pt epoch                  : {gate['latest_pt_epoch']}")
    print(f"  best.pt epoch                    : {gate['best_pt_epoch']}")
    print(f"  persisted global_step            : {gate['persisted_global_step']}")
    print(f"  epoch-28 bad_epochs              : {gate['epoch28_bad_epochs']}")
    print(f"  epoch-28 best_epoch_so_far       : {gate['epoch28_best_epoch_so_far']}")
    print(f"  replayed best epoch              : {gate['replayed_best_epoch']}")
    print(f"  replayed final bad_epochs        : {gate['replayed_final_bad_epochs']}")
    print(f"  replay mismatches                : {len(gate['replay_mismatches'])}")
    for item in gate["replay_mismatches"][:10]:
        print("     -", item)
    print()
    print(f"  PRE_REPAIR_PRIMARY_SELECTION_VALIDATED = "
          f"{gate['PRE_REPAIR_PRIMARY_SELECTION_VALIDATED']}")
    print(f"  reason: {gate['primary_validity_reason']}")

    if "--write-artifact" in sys.argv:
        if not (hashes_ok and gate["PRE_REPAIR_PRIMARY_SELECTION_VALIDATED"]):
            print("\nREFUSING to write §17 artifact: gate has not passed.")
            return 1
        payload = {
            "artifact": "PHASE13_PART1B_PRE_REPAIR_PRIMARY_SELECTION_VALIDATION",
            "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "experiment_id": EXP,
            "conclusion": "EPOCHS_1_28_PRIMARY_CHECKPOINT_SELECTION_VALID",
            "reason": (
                "all 28 completed epochs emitted zero proposals, therefore frozen "
                "primary coverage terms were invariant to the component-mask "
                "implementation bug"
            ),
            "secondary_diagnostic_history": "NOT_CANONICAL_PRE_R2B",
            "history_rows_disposition": "PRESERVED_UNMODIFIED",
            "history_rows": gate["history_rows"],
            "epochs_contiguous": gate["epochs_contiguous_1_to_N"],
            "best_epoch_through_28": gate["replayed_best_epoch"],
            "bad_epochs_after_28": gate["epoch28_bad_epochs"],
            "pre_stop_evidence_unchanged": hashes_ok,
            "gate": gate,
            "disclaimer": (
                "This does NOT claim the pre-repair evaluator was correct. It claims "
                "only that its defect could not alter the primary tuple while there "
                "were zero proposals."
            ),
            "no_training": True,
            "no_model": True,
            "no_cuda": True,
            "test_reads": 0,
        }
        OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        OUT_MD.write_text(
            "# PHASE-13 PART-1B — PRE-REPAIR PRIMARY SELECTION VALIDATION\n\n"
            f"- conclusion: **EPOCHS_1_28_PRIMARY_CHECKPOINT_SELECTION_VALID**\n"
            f"- history rows: {gate['history_rows']} (contiguous: "
            f"{gate['epochs_contiguous_1_to_N']})\n"
            f"- best epoch through 28: **{gate['replayed_best_epoch']}**\n"
            f"- bad_epochs after 28: **{gate['epoch28_bad_epochs']}**\n"
            "- secondary diagnostic history: **NOT_CANONICAL_PRE_R2B**\n"
            "- history rows: **PRESERVED_UNMODIFIED**\n\n"
            "All 28 completed epochs emitted zero proposals, so the frozen primary\n"
            "coverage terms were invariant to the component-mask implementation bug.\n\n"
            "This does **not** claim the pre-repair evaluator was correct — only that\n"
            "its defect could not alter the primary tuple while proposals were zero.\n",
            encoding="utf-8",
        )
        print(f"\nwrote {OUT_JSON}")
        print(f"wrote {OUT_MD}")

    return 0 if (hashes_ok and gate["PRE_REPAIR_PRIMARY_SELECTION_VALIDATED"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
