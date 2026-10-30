"""Transform the v2-era Phase-14 diagnostic into the clean-v3 adapted evaluator.

Copies scripts/evaluation/evaluate_phase14_diagnostic.py verbatim, then applies
TARGETED clean-v3 bindings. All metric/fusion semantics are preserved byte-for-byte;
only population, checkpoints, SHAs, and population-dependent denominators change.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "evaluation" / "evaluate_phase14_diagnostic.py"
DST = ROOT / "scripts" / "evaluation" / "evaluate_phase14_clean_v3_diagnostic.py"

text = SRC.read_text(encoding="utf-8")

repls = []

def add(old, new, count=1):
    repls.append((old, new, count))

# --- docstring ---
add(
    "Evaluates GLOBAL_ONLY, ORACLE_REGIONAL, and PREDICTED_REGIONAL on the 106 KUB FULL_FIELD VAL images.",
    "Evaluates GLOBAL_ONLY, ORACLE_REGIONAL, and PREDICTED_REGIONAL on the 103 KUB FULL_FIELD clean-v3 VAL images.",
)

# --- manifest guard import + call ---
add(
    "from src.utils.manifest_guard import verify_manifests",
    "from src.utils.manifest_guard import verify_manifests, validate_manifest_version_strict",
)
add("    verify_manifests()", '    validate_manifest_version_strict("phase4_v3")')

# --- table paths ---
add(
    '    val_samples_path = tables_dir / "kub_val_samples_sized.csv"\n'
    '    val_comps_path = tables_dir / "kub_val_components_sized.csv"\n'
    '    p13_comps_path = tables_dir / "phase13_predicted_roi_per_component.csv"\n'
    '    p12_imgs_path = tables_dir / "phase12_oracle_roi_per_image.csv"',
    '    val_samples_path = tables_dir / "kub_val_samples_sized_clean_v3.csv"\n'
    '    val_comps_path = tables_dir / "kub_val_components_sized_clean_v3.csv"\n'
    '    p13_comps_path = tables_dir / "phase13_clean_v3_hard_tiny_replication_set.csv"\n'
    '    p12_imgs_path = tables_dir / "phase13_clean_v3_global_empty_replication_set.csv"',
)

# --- checkpoint paths ---
add(
    '    global_ckpt_path = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512" / "best.pt"\n'
    '    regional_ckpt_path = (\n'
    '        PROJECT_ROOT / "checkpoints" / "phase14_diag_regional_unet_oracletrain_a3_seed42_v1" / "best.pt"\n'
    '    )\n'
    '    localizer_ckpt_path = (\n'
    '        PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1" / "best.pt"\n'
    '    )',
    '    global_ckpt_path = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"\n'
    '    regional_ckpt_path = (\n'
    '        PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"\n'
    '    )\n'
    '    localizer_ckpt_path = (\n'
    '        PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3" / "best.pt"\n'
    '    )',
)

# --- expected SHAs ---
add(
    '    expected_sha_global = "4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d"\n'
    '    expected_sha_regional = "89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0"\n'
    '    expected_sha_localizer = "ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace"',
    '    expected_sha_global = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"\n'
    '    expected_sha_regional = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"\n'
    '    expected_sha_localizer = "7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273"',
)

# --- population assertions ---
add('assert len(ff_samples) == 106, f"Expected 106 FULL_FIELD samples, got {len(ff_samples)}"',
    'assert len(ff_samples) == 103, f"Expected 103 clean-v3 FULL_FIELD samples, got {len(ff_samples)}"')
add('assert len(ff_components) == 156, f"Expected 156 FULL_FIELD components, got {len(ff_components)}"',
    'assert len(ff_components) == 152, f"Expected 152 clean-v3 FULL_FIELD components, got {len(ff_components)}"')
add(
    '    assert size_counts.get("TINY", 0) == 73, f"Expected 73 Tiny, got {size_counts.get(\'TINY\')}"\n'
    '    assert size_counts.get("SMALL", 0) == 29, f"Expected 29 Small, got {size_counts.get(\'SMALL\')}"\n'
    '    assert size_counts.get("MEDIUM", 0) == 36, f"Expected 36 Medium, got {size_counts.get(\'MEDIUM\')}"\n'
    '    assert size_counts.get("LARGE", 0) == 18, f"Expected 18 Large, got {size_counts.get(\'LARGE\')}"',
    '    assert size_counts.get("TINY", 0) == 72, f"Expected 72 Tiny, got {size_counts.get(\'TINY\')}"\n'
    '    assert size_counts.get("SMALL", 0) == 28, f"Expected 28 Small, got {size_counts.get(\'SMALL\')}"\n'
    '    assert size_counts.get("MEDIUM", 0) == 36, f"Expected 36 Medium, got {size_counts.get(\'MEDIUM\')}"\n'
    '    assert size_counts.get("LARGE", 0) == 16, f"Expected 16 Large, got {size_counts.get(\'LARGE\')}"',
)

# --- hard-tiny set (clean-v3 replication set) ---
add(
    '    df_p13_comps = pd.read_csv(p13_comps_path)\n'
    '    hard_tiny_rows = df_p13_comps[(df_p13_comps["kub_size_v1"] == "TINY") & (~df_p13_comps["global_detected"])]\n'
    '    assert len(hard_tiny_rows) == 16, f"Expected 16 hard-Tiny, got {len(hard_tiny_rows)}"\n'
    '    hard_tiny_set = set(zip(hard_tiny_rows["sample_id"], hard_tiny_rows["component_id"]))',
    '    df_p13_comps = pd.read_csv(p13_comps_path)\n'
    '    hard_tiny_rows = df_p13_comps[(df_p13_comps["size_stratum"] == "TINY") & (~df_p13_comps["global_detected"])]\n'
    '    assert len(hard_tiny_rows) == 15, f"Expected 15 clean-v3 hard-Tiny, got {len(hard_tiny_rows)}"\n'
    '    hard_tiny_set = set(zip(hard_tiny_rows["sample_id"], hard_tiny_rows["native_component_id"]))',
)

# --- global-empty set (clean-v3 replication set) ---
add(
    '    df_p12_imgs = pd.read_csv(p12_imgs_path)\n'
    '    global_empty_rows = df_p12_imgs[df_p12_imgs["global_empty_prediction"]]\n'
    '    assert len(global_empty_rows) == 7, f"Expected 7 global-empty images, got {len(global_empty_rows)}"\n'
    '    global_empty_set = set(global_empty_rows["sample_id"])',
    '    df_p12_imgs = pd.read_csv(p12_imgs_path)\n'
    '    global_empty_rows = df_p12_imgs[df_p12_imgs["prediction_empty"]]\n'
    '    assert len(global_empty_rows) == 5, f"Expected 5 clean-v3 global-empty images, got {len(global_empty_rows)}"\n'
    '    global_empty_set = set(global_empty_rows["sample_id"])',
)

# --- verification print ---
add(
    '    print("[Phase 14 Part 3] Verified 106 FULL_FIELD images, 156 components (73/29/36/18), 16 hard-Tiny, 7 global-empty.")',
    '    print("[Phase 14 clean-v3] Verified 103 FULL_FIELD images, 152 components (72/28/36/16), 15 hard-Tiny, 5 global-empty.")',
)
add(
    '    print("[Phase 14 Part 3] Starting frozen evaluation loop across 106 FULL_FIELD VAL images...")',
    '    print("[Phase 14 clean-v3] Starting frozen evaluation loop across 103 FULL_FIELD VAL images...")',
)

# --- denominator constants in summary_rows ---
add('            "hard_tiny_total": 16,', '            "hard_tiny_total": 15,')
add('            "global_empty_total": 7,', '            "global_empty_total": 5,')

# --- Tg/Dg: load frozen reference instead of hardcode + self-consistency ---
add(
    '    # 10. Diagnostic Contrasts & Gate Evaluations\n'
    '    # Frozen references\n'
    '    Tg = 0.780822\n'
    '    Dg = 0.652776\n'
    '\n'
    '    # Measured\n'
    '    row_g = df_summary[df_summary["mode"] == "GLOBAL_ONLY"].iloc[0]\n'
    '    row_o = df_summary[df_summary["mode"] == "ORACLE_REGIONAL"].iloc[0]\n'
    '    row_p = df_summary[df_summary["mode"] == "PREDICTED_REGIONAL"].iloc[0]\n'
    '\n'
    '    To = float(row_o["tiny_recall90"])\n'
    '    Tp = float(row_p["tiny_recall90"])\n'
    '    Do = float(row_o["mean_dice"])\n'
    '    Dp = float(row_p["mean_dice"])',
    '    # 10. Diagnostic Contrasts & Gate Evaluations\n'
    '    # Frozen GLOBAL references (clean-v3) - generated once and FROZEN in section 6.\n'
    '    ref_path = audits_dir / "phase14_clean_v3_global_reference_freeze.json"\n'
    '    assert ref_path.exists(), f"Frozen GLOBAL reference missing: {ref_path}"\n'
    '    _ref = json.load(open(ref_path))\n'
    '    assert _ref.get("status") == "FROZEN", f"GLOBAL reference not FROZEN: {_ref.get(\'status\')}"\n'
    '    Tg = float(_ref["references"]["Tg_clean_v3"])\n'
    '    Dg = float(_ref["references"]["Dg_clean_v3"])\n'
    '\n'
    '    # Measured\n'
    '    row_g = df_summary[df_summary["mode"] == "GLOBAL_ONLY"].iloc[0]\n'
    '    row_o = df_summary[df_summary["mode"] == "ORACLE_REGIONAL"].iloc[0]\n'
    '    row_p = df_summary[df_summary["mode"] == "PREDICTED_REGIONAL"].iloc[0]\n'
    '\n'
    '    To = float(row_o["tiny_recall90"])\n'
    '    Tp = float(row_p["tiny_recall90"])\n'
    '    Do = float(row_o["mean_dice"])\n'
    '    Dp = float(row_p["mean_dice"])\n'
    '\n'
    '    # Self-consistency: freshly computed GLOBAL reference must agree with the FROZEN one.\n'
    '    _fresh_Tg = float(row_g["tiny_recall90"])\n'
    '    _fresh_Dg = float(row_g["mean_dice"])\n'
    '    assert abs(_fresh_Tg - Tg) < 1e-6, f"Frozen Tg {Tg} != fresh {_fresh_Tg}"\n'
    '    assert abs(_fresh_Dg - Dg) < 1e-6, f"Frozen Dg {Dg} != fresh {_fresh_Dg}"',
)

# --- audit population dict ---
add('            "val_samples": 106,', '            "val_samples": 103,')
add('            "authoritative_components": 156,', '            "authoritative_components": 152,')
add('            "hard_tiny_denominator": 16,', '            "hard_tiny_denominator": 15,')
add('            "global_empty_denominator": 7,', '            "global_empty_denominator": 5,')

# --- audit gate condition string (JSON) ---
add(
    '            "condition": "Tp >= 0.780822 AND Dp >= 0.632776 AND Hard-Tiny >= 2/16 AND Global-Empty >= 1/7",',
    '            "condition": "Tp >= 0.780822 AND Dp >= 0.632776 AND Hard-Tiny >= 2/15 AND Global-Empty >= 1/5",',
)

# --- audit MD lines ---
add(
    '        f"- **Primary Population:** KUB FULL_FIELD VAL (106 images, 156 authoritative components)",\n'
    '        f"- **Component Size Stratification:** 73 Tiny, 29 Small, 36 Medium, 18 Large",\n'
    '        f"- **Hard Failure Cases:** 16 hard-Tiny components, 7 global-empty images",',
    '        f"- **Primary Population:** KUB FULL_FIELD clean-v3 VAL (103 images, 152 authoritative components)",\n'
    '        f"- **Component Size Stratification:** 72 Tiny, 28 Small, 36 Medium, 16 Large",\n'
    '        f"- **Hard Failure Cases:** 15 hard-Tiny components, 5 global-empty images",',
)
add('        f"  - Regional Refiner: `{sha_regional}` (epoch 14)",', '        f"  - Regional Refiner: `{sha_regional}` (epoch 56)",')
# denominator strings inside MD (file stores two backslashes for LaTeX \ge)
add(r'Hard-Tiny $\\ge 2/16$, Global-Empty $\\ge 1/7$', r'Hard-Tiny $\\ge 2/15$, Global-Empty $\\ge 1/5$')
add(r"Hard-Tiny = {row_p['hard_tiny_recovered']}/16, Global-Empty = {row_p['global_empty_recovered']}/7",
    r"Hard-Tiny = {row_p['hard_tiny_recovered']}/15, Global-Empty = {row_p['global_empty_recovered']}/5")

# --- audit JSON filename ---
add('audit_json_path = audits_dir / "phase14_part3_diagnostic_evaluation.json"',
    'audit_json_path = audits_dir / "phase14_clean_v3_diagnostic_evaluation.json"')
add('audit_md_path = audits_dir / "phase14_part3_diagnostic_evaluation.md"',
    'audit_md_path = audits_dir / "phase14_clean_v3_diagnostic_evaluation.md"')

# --- wait: cosmetic global replaces are applied AFTER the targeted loop (see below) ---

# --- apply all targeted replacements with uniqueness checks FIRST ---
for old, new, count in repls:
    n = text.count(old)
    if n != count:
        raise SystemExit(f"REPLACEMENT MISMATCH (expected {count}, got {n}):\n{old[:120]}")
    text = text.replace(old, new)

# --- cosmetic global replaces AFTER targeted ones (avoid clobbering old-strings) ---
text = text.replace("phase14_part3_", "phase14_clean_v3_")
text = text.replace('"part": "3 — Frozen Full Validation Diagnostic Evaluation"',
                    '"part": "3 — Frozen Full Validation Diagnostic Evaluation (clean-v3)"')
text = text.replace("[Phase 14 Part 3]", "[Phase 14 clean-v3]")

DST.write_text(text, encoding="utf-8")
print(f"[transform] Wrote {DST} ({len(text)} bytes); {len(repls)} replacements applied.")
