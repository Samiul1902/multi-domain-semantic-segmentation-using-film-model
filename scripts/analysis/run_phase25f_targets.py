"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §10 (supervisor ruling F4).

Build the frozen S_omega training target from the already-frozen Phase25C OOF
``delta_dice``:  y_i = 1.0 iff delta_dice_i > 0.0 else 0.0  (DeltaDice == 0
falls back). Targets are supervision only; delta_dice never enters the input.

No model construction / training / forward pass / refinement / new DeltaDice.

Outputs:
  data_cache/phase25f_barr_post_safety_v1_0/targets.csv
  reports/audits/phase25f_target_contract_v1_0.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def main() -> int:
    lab = pd.read_csv(C.PHASE25C_LABEL_CSV)
    lab["sample_id"] = lab["sample_id"].astype(str)

    feat_meta = pd.read_csv(C.CACHE25F / "metadata.csv")
    feat_meta["sample_id"] = feat_meta["sample_id"].astype(str)

    lab_by_sid = {r.sample_id: r for r in lab.itertuples(index=False)}
    assert set(lab_by_sid.keys()) == set(feat_meta["sample_id"]), "label/feature id mismatch"

    rows = []
    for r in feat_meta.itertuples(index=False):
        lr = lab_by_sid[r.sample_id]
        dd = float(lr.delta_dice)
        rows.append({
            "sample_id": r.sample_id,
            "feature_row_index": int(r.feature_row_index),
            "delta_dice": np.float32(dd),
            "safety_target": np.float32(1.0 if dd > 0.0 else 0.0),
        })
    tg = pd.DataFrame(rows).sort_values("feature_row_index").reset_index(drop=True)
    assert tg["feature_row_index"].tolist() == list(range(4957))

    # deterministic CSV text; float32-rounded values rendered as plain decimals
    def _f32(v) -> str:
        return repr(float(np.float32(v)))

    txt = "sample_id,feature_row_index,delta_dice,safety_target\n" + "".join(
        f"{r.sample_id},{int(r.feature_row_index)},"
        f"{_f32(r.delta_dice)},{_f32(r.safety_target)}\n"
        for r in tg.itertuples(index=False))
    (C.CACHE25F / "targets.csv").write_text(txt, encoding="utf-8", newline="")

    n_pos = int((tg["safety_target"] == 1.0).sum())
    n_neg = int((tg["safety_target"] == 0.0).sum())
    n_dd_zero = int((tg["delta_dice"] == 0.0).sum())
    # boundary rule check: every DeltaDice == 0 must be FALLBACK (target 0)
    zero_all_fallback = bool((tg.loc[tg["delta_dice"] == 0.0, "safety_target"] == 0.0).all())

    contract = {
        "artifact": "phase25f_target_contract_v1_0",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F4_TRAINING_TARGET",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "ruling_id": "F4",
        "frozen_target": "ACCEPT iff DeltaDice > 0",
        "definition": "y_i = 1.0 if delta_dice_i > 0.0 else 0.0",
        "boundary_rule": "DeltaDice == 0 -> FALLBACK class -> y = 0",
        "class_names": {"0": "FALLBACK_GLOBAL", "1": "ACCEPT_REFINEMENT"},
        "target_dtype": "float32",
        "target_source": "canonical Phase25C OOF delta_dice "
                         "(data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
                         "phase25c_oof_paired_gain_labels.csv)",
        "not_used": ["BENEFICIAL >= +0.02", "HARMFUL <= -0.01", "NEUTRAL"],
        "reporting_labels_only": True,
        "rows": 4957,
        "positive_count": n_pos,
        "negative_count": n_neg,
        "delta_dice_zero_count": n_dd_zero,
        "all_zero_delta_are_fallback": zero_all_fallback,
        "supervision_only": True,
        "delta_dice_forbidden_from_model_input": True,
        "targets_csv": C.bind(C.CACHE25F / "targets.csv"),
        "phase25c_label_csv": C.bind(C.PHASE25C_LABEL_CSV),
        "model_forwards": 0,
        "new_delta_dice_generated": False,
        "test_reads": 0,
        "all_pass": bool(zero_all_fallback and (n_pos + n_neg) == 4957),
    }
    C.jdump(contract, C.AUD / "phase25f_target_contract_v1_0.json")

    print(f"targets: rows=4957 pos={n_pos} neg={n_neg} delta0={n_dd_zero} "
          f"zero_all_fallback={zero_all_fallback}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
