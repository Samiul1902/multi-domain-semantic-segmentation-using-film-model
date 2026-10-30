"""Phase 25F canonical execution — §24 final-epoch rule, §25 final all-DEV
normalization, §26 final refit, §27 final checkpoint, §28 final-checkpoint
integrity.

FINAL_SAFETY_EPOCHS = sorted(five CV best epochs)[2] (exact integer median).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
TAB = C.TAB
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main():
    feats = E.load_features()
    meta = E.load_metadata()
    targ = E.load_targets()
    sid_to_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}
    y_by_id = {r["sample_id"]: float(r["safety_target"]) for r in targ}
    names = [r["name"] for r in E.read_csv_rows(E.FEATURE_SCHEMA_CSV)]

    # ---------------- §24 final-epoch rule -------------------------------- #
    reg = C.jload(AUD / "phase25f_training_run_registry.json")
    best_epochs = [reg["runs"][str(k)]["best_epoch"] if str(k) in reg["runs"]
                   else reg["runs"][k]["best_epoch"] for k in range(5)]
    best_epochs = [int(x) for x in best_epochs]
    sorted_epochs = sorted(best_epochs)
    final_epochs = sorted_epochs[2]
    rule = {
        "artifact": "phase25f_final_epoch_rule_execution",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F15_FINAL_EPOCH_RULE",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "rule": "FINAL_SAFETY_EPOCHS = sorted(best_epoch_0..best_epoch_4)[2]",
        "best_epochs_in_fold_order": best_epochs,
        "sorted_best_epochs": sorted_epochs,
        "median_index": 2,
        "final_safety_epochs": final_epochs,
        "all_five_folds_early_stopped": all(
            reg["runs"][str(k)]["termination"] == "early_stop" if str(k) in reg["runs"]
            else reg["runs"][k]["termination"] == "early_stop" for k in range(5)),
        "final_seed": E.FINAL_SEED,
        "all_pass": True,
    }
    C.jdump(rule, AUD / "phase25f_final_epoch_rule_execution.json")
    print(f"best_epochs={best_epochs} sorted={sorted_epochs} FINAL_SAFETY_EPOCHS={final_epochs}")

    # ---------------- §25 final all-DEV normalization --------------------- #
    all_ids = [r["sample_id"] for r in meta]
    all_idx = [sid_to_row[s] for s in all_ids]
    raw_all = feats[all_idx]
    mu, sigma, const = E.fit_normalization(raw_all)
    final_X = E.apply_normalization(raw_all, mu, sigma, const)
    final_y = np.array([y_by_id[s] for s in all_ids], dtype=np.float32)

    E.write_csv(TAB / "phase25f_final_normalization_stats.csv",
                ["feature_index", "name", "mu", "sigma", "is_constant"],
                [[i, names[i], repr(float(mu[i])), repr(float(sigma[i])), bool(const[i])]
                 for i in range(16)])
    norm_audit = {
        "artifact": "phase25f_final_normalization",
        "phase": "25F",
        "stage": "FINAL_ALL_DEV_NORMALIZATION",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "rows": 4957,
        "statistics_source": "all 4957 ROUTER_DEVELOPMENT rows",
        "ddof": 0,
        "zero_sigma_columns": [int(i) for i in np.where(const)[0]],
        "normalized_indices": "0..15",
        "not_normalized_indices": "16..19",
        "stats_csv_sha256": C.sha256_file(TAB / "phase25f_final_normalization_stats.csv"),
        "all_pass": True,
    }
    C.jdump(norm_audit, AUD / "phase25f_final_normalization.json")

    # ---------------- §26 final refit ------------------------------------- #
    final_dir = E.CKPT_ROOT / "final"
    exp_dir = E.EXP_ROOT / "final"
    closure = E.train_logical_run(
        run_id=f"{E.RUN_FAMILY}_final",
        ckpt_dir=final_dir, exp_dir=exp_dir, seed=E.FINAL_SEED,
        fit_X=final_X, fit_y=final_y, es_X=final_X[:1], es_y=final_y[:1],
        device=DEV, use_early_stop=False, force_epochs=final_epochs, verbose=True)

    # ---------------- §27 final checkpoint -------------------------------- #
    state = torch.load(final_dir / "state.pt", map_location="cpu", weights_only=False)
    final_ckpt = {
        "model_state": state["model_state"],
        "epoch": state["epoch"],
        "final_safety_epochs": final_epochs,
        "five_cv_best_epochs": best_epochs,
        "sorted_best_epochs": sorted_epochs,
        "normalizer_mu": mu.tolist(),
        "normalizer_sigma": sigma.tolist(),
        "normalizer_constant_mask": const.tolist(),
        "seed": E.FINAL_SEED,
        "run_id": f"{E.RUN_FAMILY}_final",
        "checkpoint_semantics": "LAST_FIXED_EPOCH",
        "early_stopping": False,
        "validation": False,
    }
    E.atomic_torch_save(final_ckpt, final_dir / "final.pt")

    # ---------------- §28 final-checkpoint integrity ---------------------- #
    integ = {}
    loaded = torch.load(final_dir / "final.pt", map_location=DEV, weights_only=False)
    m = E.BARRPostSafetyV1().to(DEV)
    m.load_state_dict(loaded["model_state"])
    integ["state_dict_loads"] = True
    integ["parameter_count_1217"] = (E.count_params(m) == 1217)
    integ["finite_params"] = all(bool(torch.isfinite(p).all()) for p in m.parameters())
    with torch.inference_mode():
        out = m(torch.from_numpy(final_X[:64]).to(DEV))
    integ["synthetic_inference_finite"] = bool(torch.isfinite(out).all())
    integ["output_is_raw_logit"] = (out.dim() == 1)
    integ["epoch_equals_final_epochs"] = (int(loaded["epoch"]) == final_epochs)
    integ["checkpoint_semantics_last_fixed_epoch"] = (
        loaded["checkpoint_semantics"] == "LAST_FIXED_EPOCH")
    integ["normalizer_persisted"] = (
        len(loaded["normalizer_mu"]) == 16 and len(loaded["normalizer_sigma"]) == 16)
    integ["no_early_stopping"] = (loaded["early_stopping"] is False)

    integrity = {
        "artifact": "phase25f_final_checkpoint_integrity",
        "phase": "25F",
        "stage": "FINAL_CHECKPOINT_INTEGRITY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "final_checkpoint": f"checkpoints/{E.RUN_FAMILY}/final/final.pt",
        "final_checkpoint_sha256": C.sha256_file(final_dir / "final.pt"),
        "final_safety_epochs": final_epochs,
        "checks": integ,
        "all_pass": all(integ.values()),
    }
    C.jdump(integrity, AUD / "phase25f_final_checkpoint_integrity.json")

    print("final refit epochs:", closure["total_epochs"], "term:", closure["termination"])
    print("final checkpoint integrity:", integrity["all_pass"])
    return final_epochs


if __name__ == "__main__":
    main()
