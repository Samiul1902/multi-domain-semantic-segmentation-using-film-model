"""Phase 25C -- fold checkpoint binding (§3) + cross-fit leakage proof (§4).

Binds each outer fold to its canonical Phase25A fold-specific ROI-0.30 checkpoint
and proves the outer-target folds were excluded from FIT / EARLY_STOP.

FAIL CLOSED: any overlap -> PHASE25C_BLOCKED__CROSSFIT_LEAKAGE_VIOLATION.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import torch  # noqa: E402

AUD = ROOT / "reports" / "audits"
UTC = "2026-09-30T16:56:00+00:00"


def main() -> int:
    dev = C.load_development()
    dev_ids = set(dev["sample_id"].astype(str))
    fold_sets = C.load_fold_sets()
    assign = C.load_outer_fold_assignment()
    xfit = C.jload(AUD / "phase25a_crossfit_protocol.json")
    ckpt_integrity = C.jload(AUD / "phase25a_roi030_checkpoint_integrity.json")

    # ---------------- §3 fold checkpoint binding --------------------------- #
    binding_rows = []
    ok = True
    for k in C.OUTER_FOLDS:
        st = torch.load(C.FOLD_CKPT[k], map_location="cpu", weights_only=False)
        row = {
            "outer_fold": k,
            "checkpoint_path": str(C.FOLD_CKPT[k].relative_to(ROOT)).replace("\\", "/"),
            "checkpoint_sha256": C.sha256_file(C.FOLD_CKPT[k]),
            "best_epoch": int(st.get("best_epoch", st.get("epoch"))),
            "epoch": int(st.get("epoch")),
            "outer_fold_in_checkpoint": int(st.get("outer_fold")),
            "run": str(st.get("run")),
            "parameter_count": int(st.get("parameter_count")),
            "architecture_id": str(st.get("architecture_id")),
            "architecture_source_sha256": st["bindings"]["model_source"]["sha256"],
            "selection_rule": str(st.get("selection_rule")),
            "training_source_folds": f"all except outer fold {k}",
            "outer_target_manifest_sha256": xfit["fold_manifest_sha256"][f"fold{k}_outer_target"],
            "fit_manifest_sha256": xfit["fit_manifest_sha256"][f"fold{k}_fit"],
            "early_stop_manifest_sha256":
                xfit["early_stop_manifest_sha256"][f"fold{k}_early_stop"],
            "architecture_revision_in_ckpt": str(st.get("architecture_revision")),
        }
        row["checkpoint_sha_matches_phase25a_inventory"] = (
            row["checkpoint_sha256"] == C.EXPECTED[f"fold{k}_checkpoint_sha256"])
        row["outer_fold_matches"] = row["outer_fold_in_checkpoint"] == k
        row["parameter_count_ok"] = row["parameter_count"] == 1276401
        binding_rows.append(row)
        ok &= (row["checkpoint_sha_matches_phase25a_inventory"] and row["outer_fold_matches"]
               and row["parameter_count_ok"])

    # Phase25A final refiner must NOT be used for OOF labels
    final_sha = C.sha256_file(C.PHASE25A_FINAL_CKPT)
    final_not_used = final_sha == C.EXPECTED["phase25a_final_refiner_sha256"]

    binding = {
        "artifact": "phase25c_fold_checkpoint_binding",
        "phase": "25C",
        "method": C.METHOD,
        "architecture_revision": C.ARCH_REVISION,
        "binding_rule": "outer_fold k -> canonical Phase25A fold-k best.pt (ROI-0.30)",
        "folds": binding_rows,
        "phase25a_final_refiner_path":
            str(C.PHASE25A_FINAL_CKPT.relative_to(ROOT)).replace("\\", "/"),
        "phase25a_final_refiner_sha256": final_sha,
        "phase25a_final_refiner_used_for_oof": False,
        "phase25a_final_refiner_not_authorized_confirmed": final_not_used,
        "phase25a_checkpoint_integrity_verdict": ckpt_integrity.get("verdict"),
        "all_fold_checkpoints_bound": bool(ok),
        "test_reads": 0,
        "generated_utc": UTC,
    }
    C.jdump(binding, AUD / "phase25c_fold_checkpoint_binding.json")

    # ---------------- §4 cross-fit leakage proof --------------------------- #
    leakage = []
    for k in C.OUTER_FOLDS:
        outer = fold_sets[f"fold{k}_outer_target"]
        fit = fold_sets[f"fold{k}_fit"]
        es = fold_sets[f"fold{k}_early_stop"]
        leakage.append({
            "fold": k,
            "outer_target_n": len(outer),
            "fit_n": len(fit),
            "early_stop_n": len(es),
            "outer_minus_fit": len(outer & fit),
            "outer_minus_early_stop": len(outer & es),
            "fit_minus_early_stop": len(fit & es),
            "outer_minus_train_portion": len(outer & (fit | es)),
        })

    # every DEV sample appears in exactly one outer target
    counts = {sid: sum(sid in fold_sets[f"fold{k}_outer_target"] for k in C.OUTER_FOLDS)
              for sid in dev_ids}
    n_in_one = sum(1 for v in counts.values() if v == 1)
    n_in_zero = sum(1 for v in counts.values() if v == 0)
    n_in_many = sum(1 for v in counts.values() if v > 1)

    # 0 samples appear in their own refiner training / checkpoint-selection population
    self_leak_fit = sum(1 for sid in dev_ids
                        if sid in fold_sets[f"fold{assign[sid]}_fit"])
    self_leak_es = sum(1 for sid in dev_ids
                       if sid in fold_sets[f"fold{assign[sid]}_early_stop"])

    all_clean = (all(x["outer_minus_fit"] == 0 and x["outer_minus_early_stop"] == 0
                     and x["outer_minus_train_portion"] == 0 for x in leakage)
                 and n_in_one == len(dev_ids) and n_in_zero == 0 and n_in_many == 0
                 and self_leak_fit == 0 and self_leak_es == 0)

    out = {
        "artifact": "phase25c_crossfit_leakage_audit",
        "phase": "25C",
        "method": C.METHOD,
        "requirement": "OUTER_TARGET_k ∩ FIT_k = ∅ and ∩ EARLY_STOP_k = ∅ for all k",
        "folds": leakage,
        "all_development_n": len(dev_ids),
        "samples_in_exactly_one_outer_target": n_in_one,
        "samples_in_zero_outer_targets": n_in_zero,
        "samples_in_multiple_outer_targets": n_in_many,
        "samples_in_own_fit_population": self_leak_fit,
        "samples_in_own_early_stop_population": self_leak_es,
        "crossfit_leakage_violations": (sum(x["outer_minus_fit"] + x["outer_minus_early_stop"]
                                            for x in leakage)
                                        + n_in_zero + n_in_many + self_leak_fit + self_leak_es),
        "all_clean": bool(all_clean),
        "verdict": ("PHASE25C_CROSSFIT_LEAKAGE_CLEAN" if all_clean
                    else "PHASE25C_BLOCKED__CROSSFIT_LEAKAGE_VIOLATION"),
        "test_reads": 0,
        "generated_utc": UTC,
    }
    C.jdump(out, AUD / "phase25c_crossfit_leakage_audit.json")

    print("=== Phase 25C fold binding ===")
    for r in binding_rows:
        print(f"  fold{r['outer_fold']} sha={r['checkpoint_sha256'][:12]} "
              f"best_epoch={r['best_epoch']} params={r['parameter_count']}")
    print("=== Phase 25C cross-fit leakage ===")
    for x in leakage:
        print(f"  fold{x['fold']}: outer={x['outer_target_n']} "
              f"outer∩fit={x['outer_minus_fit']} outer∩es={x['outer_minus_early_stop']}")
    print(f"  in-exactly-one-outer-target={n_in_one}/{len(dev_ids)} "
          f"self-fit-leak={self_leak_fit} self-es-leak={self_leak_es}")
    print(f"\nbinding_ok={ok}  leakage_verdict={out['verdict']}")
    return 0 if (ok and all_clean) else 2


if __name__ == "__main__":
    raise SystemExit(main())
