"""Derive the H2B-B2 downstream evaluation script from the H2A-B2 one.

Programmatic confined diff: every replacement is asserted, so a partial diff is impossible.
The H2A downstream tables are then joined as a frozen comparator.
"""
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SRC = ROOT / "scripts" / "inference" / "post_phase13_h2a_downstream_eval.py"
DST = ROOT / "scripts" / "inference" / "post_phase13_h2b_downstream_eval.py"

s = SRC.read_text(encoding="utf-8")


def sub(old, new, count=None):
    global s
    n = s.count(old)
    if n == 0:
        raise SystemExit(f"NOT FOUND: {old[:100]!r}")
    if count is not None and n != count:
        raise SystemExit(f"COUNT MISMATCH for {old[:80]!r}: found {n}, expected {count}")
    s = s.replace(old, new)


# ---- docstring / run identity ------------------------------------------------
sub('"""POST-PHASE-13 H2-A-B2 — Downstream regional segmentation evaluation.\n\n'
    'Uses the frozen H2A epoch-83 localizer proposals (457 proposals) against four\n'
    'frozen segmentation architectures.  Reuses the Phase-13 Part1D-B global cache.\n\n'
    'No localizer training, no localizer forward, no proposal regeneration,\n'
    'no H1 filtering, no TEST.\n\n'
    'Run id: post_phase13_h2a_downstream_epoch83_native_policy\n"""',
    '"""POST-PHASE-13 H2-B-B2 — Downstream regional segmentation evaluation.\n\n'
    'Uses the frozen H2B best-checkpoint localizer proposals (488 proposals) against four\n'
    'frozen segmentation architectures.  Reuses the Phase-13 Part1D-B global cache.\n\n'
    'No localizer training, no localizer forward, no proposal regeneration,\n'
    'no H1 filtering, no threshold search, no TEST.\n\n'
    'Run id: post_phase13_h2b_downstream_best_native_policy\n"""')
sub('RUN_ID = "post_phase13_h2a_downstream_epoch83_native_policy"',
    'RUN_ID = "post_phase13_h2b_downstream_best_native_policy"')

# ---- bindings ----------------------------------------------------------------
sub('''    "h2a_protocol": ("reports/audits/post_phase13_h2a_protocol_frozen.json",
                     "0fafc793b3a814e010e1fdd48f6a2333042985eaef4a44e0382b3991800da96b"),
    "h2a_training_eval": ("reports/audits/post_phase13_h2a_training_evaluation.json",
                          "7ecd3a04fd6bfa6051afa3bd4536566d61a81287c73f34fb2e4689d0e0587899"),''',
    '''    "h2b_protocol": ("reports/audits/post_phase13_h2b_protocol_frozen.json",
                     "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"),
    "h2b_b1_eval": ("reports/audits/post_phase13_h2b_b1_training_evaluation.json",
                    "34a52942ea4ef9da21c4aa450a925c8c59ada771e08f99ab99c3ec669c1e2175"),
    "h2b_best_pt": ("checkpoints/post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
                    "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3/best.pt",
                    "a9147ad7d1835a6e4ef8d66cc04c063db85b2f9a65585a4a34ae2acfef05f028"),
    "h2b_loss_module": ("src/losses/soft_target_focal_bce.py",
                        "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"),''')

# ---- artifact path prefixes ---------------------------------------------------
sub("post_phase13_h2a_best_checkpoint_", "post_phase13_h2b_best_checkpoint_")
sub("post_phase13_h2a_downstream_", "post_phase13_h2b_downstream_")

# ---- identifier renames (primary becomes h2b_*) -------------------------------
for a, b in (("h2a_case_cohorts", "h2b_case_cohorts"), ("h2a_case_idx", "h2b_case_idx"),
             ("h2a_comp_idx", "h2b_comp_idx"), ("h2a_metrics", "h2b_metrics"),
             ("h2a_det", "h2b_det"), ("h2a_case", "h2b_case"), ("h2a_prop", "h2b_prop"),
             ("h2a_comp", "h2b_comp"), ("h2a_predicted", "h2b_predicted"),
             ("h2a_minus_", "h2b_minus_"), ("GLOBAL_TO_H2A_", "GLOBAL_TO_H2B_"),
             ("PHASE13_TO_H2A_", "PHASE13_TO_H2B_"), ("H2A_ORACLE_", "H2B_ORACLE_"),
             ("DELTA_H2A_", "DELTA_H2B_"),
             ("h2a_localizer", "h2b_localizer")):
    sub(a, b)

# ---- counts -------------------------------------------------------------------
sub("== 457", "== 488")
sub("!= 457", "!= 488")
sub("expected 1828", "expected 1952")
sub("== 1828", "== 1952")
sub("!= 1828", "!= 1952")
sub('"proposal_count": 457,', '"proposal_count": 488,')
sub('"h2b_proposal_count": 457,', '"h2b_proposal_count": 488,')

# ---- comments ----------------------------------------------------------------
sub("# Load H2A proposal artifacts", "# Load H2B proposal artifacts")
sub("# Stage R — H2A predicted-region inference (457 x 4 = 1828 crops)",
    "# Stage R — H2B predicted-region inference (488 x 4 = 1952 crops)")
sub("Aggregate H2A per-case cohort flags", "Aggregate H2B per-case cohort flags")
sub("H2A uses tighter tolerance since it's pure cache reuse",
    "pure cache reuse -> tight tolerance")

# ---- residual primary-side naming (these are H2B columns, not comparators) ----
sub("h2a_geom_from_row", "h2b_geom_from_row")
sub("H2A case rows", "H2B case rows")
sub("H2A proposal rows", "H2B proposal rows")
sub("H2A component rows", "H2B component rows")
sub("# Add H2A proposal score stats where available", "# Add H2B proposal score stats where available")
sub('"h2a_coverage_fraction"', '"h2b_coverage_fraction"')
sub('"h2a_covered90"', '"h2b_covered90"')
sub('"h2a_covered50"', '"h2b_covered50"')
sub('"h2a_any_overlap"', '"h2b_any_overlap"')
sub("D_H2A", "D_H2B")
sub('"mean_h2a_fp"', '"mean_h2b_fp"')
sub('"mean_h2a_fn"', '"mean_h2b_fn"')

# ---- add the frozen H2A-B2 downstream comparator ------------------------------
sub('''    p12comp = pd.read_csv(TABLES / "phase12_clean_v3_oracle_component_metrics.csv")''',
    '''    # Frozen H2A-B2 downstream comparator (physically present -> include it).
    H2A_CMP_AVAILABLE = True
    h2a_cmp_case = pd.read_csv(TABLES / "post_phase13_h2a_downstream_case_model_metrics.csv")
    h2a_cmp_case_idx = h2a_cmp_case.set_index(["model", "sample_id"])
    assert len(h2a_cmp_case_idx) == 412, len(h2a_cmp_case_idx)
    h2a_cmp_comp = pd.read_csv(TABLES / "post_phase13_h2a_downstream_component_model_metrics.csv")
    h2a_cmp_comp_idx = h2a_cmp_comp.set_index(["model", "sample_id", "native_component_id"])
    assert len(h2a_cmp_comp_idx) == 608, len(h2a_cmp_comp_idx)
    print("H2A downstream comparator: AVAILABLE", flush=True)

    p12comp = pd.read_csv(TABLES / "phase12_clean_v3_oracle_component_metrics.csv")''')

# case row: add H2A comparator metrics + deltas
sub('''            # Deltas
            for f in ("dice", "iou", "precision", "recall"):
                row[f"h2b_minus_global_{f}"] = row[f"h2b_predicted_{f}"] - row[f"global_{f}"]
                row[f"h2b_minus_phase13_{f}"] = row[f"h2b_predicted_{f}"] - row[f"phase13_predicted_{f}"]
                row[f"h2b_minus_oracle_{f}"] = row[f"h2b_predicted_{f}"] - row[f"oracle_{f}"]
                row[f"oracle_minus_global_{f}"] = row[f"oracle_{f}"] - row[f"global_{f}"]''',
    '''            # Frozen H2A-B2 downstream comparator
            h2ac = h2a_cmp_case_idx.loc[(key, sid)]
            for f in ("dice", "iou", "precision", "recall"):
                row[f"h2a_predicted_{f}"] = float(h2ac[f"h2a_predicted_{f}"])
            for f in ("tp_pixels", "fp_pixels", "fn_pixels"):
                row[f"h2a_predicted_{f}"] = float(h2ac[f"h2a_predicted_{f}"])
            row["h2a_predicted_prediction_empty"] = bool(h2ac["h2a_predicted_prediction_empty"])

            # Deltas
            for f in ("dice", "iou", "precision", "recall"):
                row[f"h2b_minus_global_{f}"] = row[f"h2b_predicted_{f}"] - row[f"global_{f}"]
                row[f"h2b_minus_phase13_{f}"] = row[f"h2b_predicted_{f}"] - row[f"phase13_predicted_{f}"]
                row[f"h2b_minus_h2a_{f}"] = row[f"h2b_predicted_{f}"] - row[f"h2a_predicted_{f}"]
                row[f"h2b_minus_oracle_{f}"] = row[f"h2b_predicted_{f}"] - row[f"oracle_{f}"]
                row[f"oracle_minus_global_{f}"] = row[f"oracle_{f}"] - row[f"global_{f}"]''')

sub('''            row["case_dice_unchanged_vs_phase13"] = bool(abs(row["h2b_predicted_dice"] - row["phase13_predicted_dice"]) <= DICE_TOL)''',
    '''            row["case_dice_unchanged_vs_phase13"] = bool(abs(row["h2b_predicted_dice"] - row["phase13_predicted_dice"]) <= DICE_TOL)
            row["case_dice_improved_vs_h2a"] = bool(row["h2b_predicted_dice"] > row["h2a_predicted_dice"] + DICE_TOL)
            row["case_dice_worsened_vs_h2a"] = bool(row["h2b_predicted_dice"] < row["h2a_predicted_dice"] - DICE_TOL)
            row["case_dice_unchanged_vs_h2a"] = bool(abs(row["h2b_predicted_dice"] - row["h2a_predicted_dice"]) <= DICE_TOL)''')

# component row: add H2A comparator detection + recovery/loss
sub('''                hd = bool(h2b_det[(key, sid, cid)])''',
    '''                hd = bool(h2b_det[(key, sid, cid)])
                h2ad = bool(h2a_cmp_comp_idx.loc[(key, sid, cid)]["h2a_predicted_detected"])''')
sub('''                    "PHASE13_TO_H2B_LOSS": bool(p13d and (not hd)),
                })''',
    '''                    "PHASE13_TO_H2B_LOSS": bool(p13d and (not hd)),
                    "h2a_predicted_detected": h2ad,
                    "H2A_TO_H2B_RECOVERY": bool((not h2ad) and hd),
                    "H2A_TO_H2B_LOSS": bool(h2ad and (not hd)),
                })''')

# model summary: add H2A comparator columns
sub('''        D_H2B = float(sub["h2b_predicted_dice"].mean())''',
    '''        D_H2B = float(sub["h2b_predicted_dice"].mean())
        D_H2A = float(sub["h2a_predicted_dice"].mean())''')
sub('''            "DELTA_H2B_PHASE13_DICE": D_H2B - D_P13,''',
    '''            "DELTA_H2B_PHASE13_DICE": D_H2B - D_P13,
            "h2a_predicted_macro_dice": D_H2A,
            "h2a_predicted_macro_iou": float(sub["h2a_predicted_iou"].mean()),
            "h2a_predicted_macro_precision": float(sub["h2a_predicted_precision"].mean()),
            "h2a_predicted_macro_recall": float(sub["h2a_predicted_recall"].mean()),
            "mean_h2a_fp": float(sub["h2a_predicted_fp_pixels"].mean()),
            "mean_h2a_fn": float(sub["h2a_predicted_fn_pixels"].mean()),
            "DELTA_H2B_H2A_DICE": D_H2B - D_H2A,''')
sub('''            "component_losses_vs_phase13": int(comps["PHASE13_TO_H2B_LOSS"].sum()),''',
    '''            "component_losses_vs_phase13": int(comps["PHASE13_TO_H2B_LOSS"].sum()),
            "component_recoveries_vs_h2a": int(comps["H2A_TO_H2B_RECOVERY"].sum()),
            "component_losses_vs_h2a": int(comps["H2A_TO_H2B_LOSS"].sum()),
            "fp_delta_vs_h2a": float((sub["h2b_predicted_fp_pixels"] - sub["h2a_predicted_fp_pixels"]).mean()),
            "cases_improved_vs_h2a": int(sub["case_dice_improved_vs_h2a"].sum()),
            "cases_same_vs_h2a": int(sub["case_dice_unchanged_vs_h2a"].sum()),
            "cases_worse_vs_h2a": int(sub["case_dice_worsened_vs_h2a"].sum()),''')

# ---- cross-architecture naming + H2A comparator -------------------------------
for a in ("cases_h2a_improved_vs_global_all4", "cases_h2a_nonworse_vs_global_all4",
          "cases_h2a_worse_vs_global_all4", "cases_h2a_improved_vs_phase13_all4",
          "cases_h2a_worse_vs_phase13_all4"):
    sub(f'"{a}"', f'"{a.replace("h2a_", "h2b_")}"')

sub('''    piv_wor_p = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_worsened_vs_phase13", aggfunc="first")''',
    '''    piv_wor_p = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_worsened_vs_phase13", aggfunc="first")
    piv_imp_h = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_improved_vs_h2a", aggfunc="first")
    piv_wor_h = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_worsened_vs_h2a", aggfunc="first")''')
sub('''        "components_lost_vs_global_by_all4": int((comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_H2B_LOSS"].sum() == 4).sum()),
    }''',
    '''        "components_lost_vs_global_by_all4": int((comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_H2B_LOSS"].sum() == 4).sum()),
        "cases_h2b_improved_vs_h2a_all4": int((piv_imp_h.sum(axis=1) == 4).sum()),
        "cases_h2b_worse_vs_h2a_all4": int((piv_wor_h.sum(axis=1) == 4).sum()),
    }''')

# ---- rewrite the localizer->downstream translation table (3 localizer families) ----
_start = s.index("    # Load H2A standalone localizer metrics")
_end = s.index('    pd.DataFrame(link_rows).to_csv(TABLES / "post_phase13_h2b_localizer_to_downstream_comparison.csv", index=False)')
NEW_LINK = '''    # Frozen localizer metrics for all three localizer families.
    h2b_localizer = json.loads(
        (AUDITS / "post_phase13_h2b_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]
    h2a_localizer = json.loads(
        (AUDITS / "post_phase13_h2a_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]

    link_rows = []
    for key in MODELS:
        sub = case_df[case_df["model"] == key]
        comps = comp_df[comp_df["model"] == key]
        link_rows.append({
            "model": key,
            "model_display": DISPLAY[key],
            # --- H2B localizer (frozen B1 best checkpoint) ---
            "h2b_proposal_count": 488,
            "h2b_pixel_any_hit_precision": h2b_localizer["proposal_pixel_any_hit_precision"],
            "h2b_bbox_any_hit_precision": h2b_localizer["proposal_bbox_any_hit_precision"],
            "h2b_tiny90": h2b_localizer["tiny_recall90"],
            "h2b_overall90": h2b_localizer["overall_recall90"],
            "h2b_overall50": h2b_localizer["overall_recall50"],
            "h2b_any_overlap": h2b_localizer["any_overlap_recall"],
            "h2b_mean_coverage": h2b_localizer["mean_coverage"],
            "h2b_mean_union_area": h2b_localizer["mean_proposal_union_area"],
            "h2b_score_max": h2b_localizer["score_max"],
            "h2b_score_iqr": h2b_localizer["score_iqr"],
            "h2b_fraction_at_max": h2b_localizer["fraction_exactly_at_max"],
            "h2b_roc_auc": h2b_localizer["roc_auc_score_to_pixel_any_hit"],
            "h2b_pr_auc": h2b_localizer["pr_auc_score_to_pixel_any_hit"],
            # --- H2A localizer (frozen) ---
            "h2a_proposal_count": 457,
            "h2a_pixel_any_hit_precision": h2a_localizer["proposal_pixel_any_hit_precision"],
            "h2a_bbox_any_hit_precision": h2a_localizer["proposal_bbox_any_hit_precision"],
            "h2a_tiny90": h2a_localizer["tiny_recall90"],
            "h2a_overall90": h2a_localizer["overall_recall90"],
            "h2a_overall50": h2a_localizer["overall_recall50"],
            "h2a_any_overlap": h2a_localizer["any_overlap_recall"],
            "h2a_mean_coverage": h2a_localizer["mean_coverage"],
            "h2a_mean_union_area": h2a_localizer["mean_proposal_union_area"],
            "h2a_score_max": h2a_localizer["score_max"],
            "h2a_score_iqr": h2a_localizer["score_iqr"],
            "h2a_fraction_at_max": h2a_localizer["fraction_exactly_at_max"],
            "h2a_roc_auc": h2a_localizer["roc_auc_score_to_pixel_any_hit"],
            "h2a_pr_auc": h2a_localizer["pr_auc_score_to_pixel_any_hit"],
            # --- Phase13 localizer (historical context) ---
            "phase13_proposal_count": 494,
            "phase13_pixel_any_hit_precision": 0.24696356275303644,
            "phase13_bbox_any_hit_precision": 0.24898785425101214,
            "phase13_tiny90": 0.6805555555555556,
            "phase13_overall90": 0.5986842105263158,
            "phase13_overall50": 0.7894736842105263,
            "phase13_any_overlap": 0.8486842105263158,
            "phase13_mean_coverage": 0.7584022780771768,
            "phase13_mean_union_area": 0.004846047236646118,
            "phase13_score_max": 0.1250653713941574,
            "phase13_score_iqr": 0.0005326690673828125,
            "phase13_fraction_at_max": 0.6821862348178138,
            # --- Downstream (this run) ---
            "h2b_macro_dice": float(sub["h2b_predicted_dice"].mean()),
            "h2b_macro_iou": float(sub["h2b_predicted_iou"].mean()),
            "h2b_macro_precision": float(sub["h2b_predicted_precision"].mean()),
            "h2b_macro_recall": float(sub["h2b_predicted_recall"].mean()),
            "h2b_mean_fp": float(sub["h2b_predicted_fp_pixels"].mean()),
            "h2b_mean_fn": float(sub["h2b_predicted_fn_pixels"].mean()),
            "h2b_component_recoveries_vs_global": int(comps["GLOBAL_TO_H2B_RECOVERY"].sum()),
            "h2b_component_losses_vs_global": int(comps["GLOBAL_TO_H2B_LOSS"].sum()),
            # --- Downstream (frozen comparators) ---
            "h2a_macro_dice": float(sub["h2a_predicted_dice"].mean()),
            "h2a_macro_precision": float(sub["h2a_predicted_precision"].mean()),
            "h2a_macro_recall": float(sub["h2a_predicted_recall"].mean()),
            "h2a_mean_fp": float(sub["h2a_predicted_fp_pixels"].mean()),
            "h2a_mean_fn": float(sub["h2a_predicted_fn_pixels"].mean()),
            "phase13_macro_dice": float(sub["phase13_predicted_dice"].mean()),
            "phase13_macro_precision": float(sub["phase13_predicted_precision"].mean()),
            "phase13_macro_recall": float(sub["phase13_predicted_recall"].mean()),
            "phase13_mean_fp": float(sub["phase13_predicted_fp_pixels"].mean()),
            "phase13_mean_fn": float(sub["phase13_predicted_fn_pixels"].mean()),
        })
'''
s = s[:_start] + NEW_LINK + s[_end:]

# ---- integrity audit identity -------------------------------------------------
sub('"artifact": "POST_PHASE13_H2A_DOWNSTREAM_INTEGRITY"',
    '"artifact": "POST_PHASE13_H2B_B2_DOWNSTREAM_INTEGRITY"')
sub('''        "h2a_protocol_sha": bind["h2a_protocol"]["sha"],
        "h2a_training_eval_sha": bind["h2a_training_eval"]["sha"],
        "h2a_best_pt_sha": bind["ckpt_unet"]["sha"],  # placeholder, actual is in training eval''',
    '''        "h2b_protocol_sha": bind["h2b_protocol"]["sha"],
        "h2b_b1_evaluation_sha": bind["h2b_b1_eval"]["sha"],
        "h2b_best_pt_sha": bind["h2b_best_pt"]["sha"],
        "h2b_loss_module_sha": bind["h2b_loss_module"]["sha"],
        "h2a_downstream_comparator": "AVAILABLE",
        "h2a_comparator_case_sha": sha256_file(TABLES / "post_phase13_h2a_downstream_case_model_metrics.csv"),
        "h2a_comparator_component_sha": sha256_file(TABLES / "post_phase13_h2a_downstream_component_model_metrics.csv"),
        "phase12_oracle_case_sha": sha256_file(TABLES / "phase12_clean_v3_oracle_case_metrics.csv"),
        "phase13_predicted_case_sha": sha256_file(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv"),''')
sub('md = ["# POST-PHASE-13 H2-A-B2 — Downstream Integrity Audit", "",',
    'md = ["# POST-PHASE-13 H2-B-B2 — Downstream Integrity Audit", "",')
sub('''          f"- H2A protocol: `{bind['h2a_protocol']['sha']}`",''',
    '''          f"- H2B protocol: `{bind['h2b_protocol']['sha']}`",
          f"- H2B B1 evaluation: `{bind['h2b_b1_eval']['sha']}`",
          f"- H2B best.pt: `{bind['h2b_best_pt']['sha']}`",
          f"- H2B loss module: `{bind['h2b_loss_module']['sha']}`",''')
sub('f"**next_action: WAIT_FOR_SUPERVISOR_H2A_OUTCOME_ADJUDICATION_AUTHORIZATION**", ""]',
    'f"**next_action: WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION**", ""]')
sub('print("\\n=== H2A-B2 COMPLETE ===", flush=True)',
    'print("\\n=== H2B-B2 COMPLETE ===", flush=True)')
sub('''    """Reconstruct full geometry dict from H2A proposal table columns.

    H2A proposals store only clip_* and crop_side_pixels; pads are zero because''',
    '''    """Reconstruct full geometry dict from a frozen proposal table's columns.

    The frozen proposal tables store only clip_* and crop_side_pixels; pads are zero because''')

# ---- normalise the Phase-13 predicted comparator schema + fail fast -----------
sub('''    p13case = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    p13 = p13case.set_index(["model", "sample_id"])
    assert len(p13) == 412''',
    '''    p13case = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    # The Phase-13 predicted table stores its metrics with a ``predicted_`` prefix;
    # normalise them to the canonical bare metric names used by the comparator loop.
    _p13_metrics = ["dice", "iou", "precision", "recall", "tp_pixels", "fp_pixels", "fn_pixels",
                    "prediction_empty", "hd95", "hd95_valid", "hd95_invalid_reason",
                    "detected_native_components", "missed_native_components", "object_recall"]
    _missing = [m for m in _p13_metrics if f"predicted_{m}" not in p13case.columns]
    if _missing:
        raise RuntimeError(f"phase13 predicted table missing predicted_ columns: {_missing}")
    p13case = p13case.rename(columns={f"predicted_{m}": m for m in _p13_metrics})
    p13 = p13case.set_index(["model", "sample_id"])
    assert len(p13) == 412''')

sub('''    print("H2A downstream comparator: AVAILABLE", flush=True)''',
    '''    print("H2A downstream comparator: AVAILABLE", flush=True)

    # Fail fast on comparator schema problems BEFORE any GPU compute.
    _REQ_CASE = ["dice", "iou", "precision", "recall", "tp_pixels", "fp_pixels", "fn_pixels",
                 "prediction_empty", "hd95", "hd95_valid", "hd95_invalid_reason",
                 "detected_native_components", "missed_native_components", "object_recall"]
    for _name, _idx in (("p12_global", gn), ("p12_oracle", on), ("phase13", p13)):
        _cols = set(_idx.reset_index().columns)
        _miss = [c for c in _REQ_CASE if c not in _cols]
        if _miss:
            raise RuntimeError(f"comparator {_name} missing case columns: {_miss}")
    _h2a_req = [f"h2a_predicted_{c}" for c in ("dice", "iou", "precision", "recall",
                                               "tp_pixels", "fp_pixels", "fn_pixels",
                                               "prediction_empty")]
    _miss = [c for c in _h2a_req if c not in h2a_cmp_case.columns]
    if _miss:
        raise RuntimeError(f"H2A comparator missing columns: {_miss}")
    if "h2a_predicted_detected" not in h2a_cmp_comp.columns:
        raise RuntimeError("H2A comparator component table missing h2a_predicted_detected")
    print("comparator schema pre-flight: PASS", flush=True)''')

# ---- audit filename must be the H2B-B2 canonical name (SEC 18) ----------------
sub('post_phase13_h2b_downstream_integrity.json',
    'post_phase13_h2b_b2_downstream_integrity.json')
sub('post_phase13_h2b_downstream_integrity.md',
    'post_phase13_h2b_b2_downstream_integrity.md')

DST.write_text(s, encoding="utf-8", newline="\n")
print("wrote", DST)
print("lines:", len(s.splitlines()))
