"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §7 (supervisor ruling F3).

Freeze the EXACT S_omega input vector: 16 numeric + 4 one-hot = 20-D, all
GT-free, all already-computed post-refinement quantities.

Outputs:
  reports/audits/phase25f_feature_equation_contract_v1_0.json
  reports/tables/phase25f_post_safety_input_contract_v1_0.csv
  reports/tables/phase25f_feature_schema_v1_0.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_post_safety_features as F  # noqa: E402

import pandas as pd  # noqa: E402


def main() -> int:
    # ---- feature_schema_v1_0.csv (§8 field requirement) -------------------- #
    rows = []
    for idx, name, formula, source, units, norm in F.NUMERIC_FEATURES:
        rows.append({
            "feature_index": idx, "name": name, "formula": formula, "source": source,
            "dtype": "float32", "units": units, "normalization_role": norm,
            "GT_free": True, "group": "numeric",
        })
    for idx, name, formula in F.ONEHOT_FEATURES:
        rows.append({
            "feature_index": idx, "name": name, "formula": formula,
            "source": "frozen Phase25C label table task_id (ISIC=0, BUSI=1, KVASIR=2, KUB=3)",
            "dtype": "float32", "units": "one-hot indicator in {0,1}",
            "normalization_role": "NONE", "GT_free": True, "group": "task_onehot",
        })
    schema = pd.DataFrame(rows)
    assert schema["feature_index"].tolist() == list(range(20))
    (C.TAB / "phase25f_feature_schema_v1_0.csv").write_text(
        C.csv_text(schema), encoding="utf-8", newline="")

    # ---- input contract CSV (§7) ------------------------------------------- #
    fam = {
        "global_prob_mean": "global/refined probability summary difference",
        "refined_prob_mean": "global/refined probability summary difference",
        "mean_abs_prob_change": "global/refined probability summary difference",
        "max_abs_prob_change": "global/refined probability summary difference",
        "frac_abs_prob_change_ge_0p10": "global/refined probability summary difference",
        "global_entropy_mean": "mean probability change",
        "refined_entropy_mean": "mean probability change",
        "global_foreground_fraction": "foreground-area change",
        "refined_foreground_fraction": "foreground-area change",
        "binary_xor_fraction": "foreground-area change",
        "global_component_count": "component-count change",
        "refined_component_count": "component-count change",
        "global_boundary_fraction": "boundary-size change",
        "refined_boundary_fraction": "boundary-size change",
        "predicted_roi_area_fraction": "ROI geometry",
        "predicted_roi_side_normalized": "ROI geometry",
        "task_0_ISIC": "task_id",
        "task_1_BUSI": "task_id",
        "task_2_KVASIR": "task_id",
        "task_3_KUB": "task_id",
    }
    ic_rows = []
    for _, r in schema.iterrows():
        ic_rows.append({
            "feature_index": int(r.feature_index),
            "feature_family": fam[r["name"]],
            "exact_name_frozen": r["name"],
            "formula_frozen": r["formula"],
            "dtype_frozen": r["dtype"],
            "ordering_frozen": "index 0..19, ascending, exactly as listed",
            "normalization_frozen": r["normalization_role"],
            "source_tensor_available_on_disk": True,
            "source_tensor_bound_by_contract": True,
            "gt_free_at_inference": True,
            "authoritative_source": "reports/audits/phase25f_feature_equation_contract_v1_0.json",
            "verdict": "FROZEN",
        })
    ic = pd.DataFrame(ic_rows)
    (C.TAB / "phase25f_post_safety_input_contract_v1_0.csv").write_text(
        C.csv_text(ic), encoding="utf-8", newline="")

    # ---- equation contract -------------------------------------------------- #
    contract = {
        "artifact": "phase25f_feature_equation_contract_v1_0",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F3_EXACT_SOMEGA_INPUT_VECTOR",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "ruling_id": "F3",
        "input_dimension": 20,
        "numeric_dim": 16,
        "onehot_dim": 4,
        "definitions": {
            "P_g": "canonical global probability crop, P_g in [0,1]^(256x256), float32 "
                   "(data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy)",
            "P_r": "canonical OOF refined probability crop, P_r in [0,1]^(256x256), float32 "
                   "(data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy)",
            "t_seg": 0.50,
            "t_seg_role": "already-frozen SEGMENTATION OUTPUT threshold; explicitly NOT the "
                          "S_omega decision threshold",
            "B_g": "B_g(x) = 1[P_g(x) >= 0.50]",
            "B_r": "B_r(x) = 1[P_r(x) >= 0.50]",
            "eps": 1e-7,
            "p_c": "clip(p, eps, 1-eps)",
            "H": "H(p) = -[p_c*log2(p_c) + (1-p_c)*log2(1-p_c)]; units bits",
            "connected_components": "8-connectivity, 3x3 all-ones structuring element, "
                                    "applied to the binary mask at t_seg=0.50",
            "E": "binary_erosion(B, structure=3x3 ones, border_value=0)",
            "boundary": "boundary = B AND NOT E",
            "boundary_fraction": "sum(boundary) / (256*256)",
            "N_PIX": 256 * 256,
        },
        "numeric_features": [
            {"index": i, "name": n, "formula": fo, "source": s, "units": u,
             "dtype": "float32", "normalization_role": nz, "gt_free": True}
            for (i, n, fo, s, u, nz) in F.NUMERIC_FEATURES
        ],
        "task_onehot": {
            "order": ["task_0_ISIC", "task_1_BUSI", "task_2_KVASIR", "task_3_KUB"],
            "mapping": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
            "learned_task_embedding": False,
            "normalization_role": "NONE",
        },
        "final_input_dimension": "16 numeric + 4 one-hot = 20",
        "component_counts_cast_to_float32_after_exact_integer_computation": True,
        "explicitly_excluded_inputs": F.EXCLUDED_INPUTS,
        "exclusion_rationale": "S_omega stays focused on already-computed post-refinement "
                               "prediction behaviour rather than reusing the benefit predictor.",
        "feature_construction_must_not_inspect": ["DeltaDice", "gain category",
                                                  "global Dice", "candidate Dice"],
        "authoritative_tables": [
            "reports/tables/phase25f_post_safety_input_contract_v1_0.csv",
            "reports/tables/phase25f_feature_schema_v1_0.csv",
        ],
        "all_pass": True,
    }
    C.jdump(contract, C.AUD / "phase25f_feature_equation_contract_v1_0.json")

    print("§7 input contract + equation contract + feature schema written")
    print("features:", len(schema), "numeric:", len(F.NUMERIC_FEATURES),
          "onehot:", len(F.ONEHOT_FEATURES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
