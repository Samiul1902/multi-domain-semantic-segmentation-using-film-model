"""Phase 24 — SPECIFICATION COMPLETENESS REPAIR (3/5).

Freeze the PRIMARY router feature set (§13) by mapping each requested literal name to its
EXACT authoritative equivalent in reports/tables/phase24_router_input_contract.csv, and
freeze the module/envelope tables plus the OOF gain schema (schema only).

DESIGN ONLY. No outcome-driven selection. No training, inference or outcome inspection.

Writes:
    reports/tables/phase24_router_primary_feature_set.csv
    reports/tables/phase24_spec_module_envelope.csv
    reports/tables/phase25_future_oof_gain_schema.csv   (SCHEMA ONLY - no rows)

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase24_feature_set.py
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
TAB = ROOT / "reports" / "tables"
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()


def rows(p: Path) -> list[dict]:
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


contract = rows(TAB / "phase24_router_input_contract.csv")
allowed = [r for r in contract if r["allowed"] == "true"]
allowed_names = {r["feature"] for r in allowed}
by_name = {r["feature"]: r for r in allowed}

# ---------------------------------------------------------------------------
# §13 mapping: requested literal -> exact authoritative contract feature.
# Every mapping is justified by the contract's own reason/definition; nothing is
# invented. Where a requested notion is NOT represented in the contract, it is
# marked NEW_AUTHORITATIVE_ADDITION with an explicit derivation, still GT-free.
# ---------------------------------------------------------------------------
MAPPING = [
    # (requested_literal, group, contract_feature, mapping_kind, derivation)
    ("bridge_global_pool", "tap", "global_encoder_pooled_features", "DIRECT",
     "the bridge tap is the deepest shared bottleneck; it is summarised by the global "
     "encoder pooled-feature axis already allowed"),
    ("bridge_roi_pool", "tap", "roi_pooled_global_features", "DIRECT",
     "ROI-aware pooling of the same global forward, already allowed"),
    ("decoder2_global_pool", "tap", "global_decoder_pooled_features", "DIRECT",
     "the decoder tap is summarised by the allowed global decoder pooled-feature axis"),
    ("decoder2_roi_pool", "tap", "roi_pooled_global_features", "SHARED_AXIS",
     "the ROI pooling is computed per tap on the SAME forward; the contract exposes a single "
     "ROI-pooled axis which is instantiated once per tap (3 ROI axes total)"),
    ("decoder1_global_pool", "tap", "global_decoder_pooled_features", "SHARED_AXIS",
     "the second decoder tap reuses the allowed global decoder pooled axis (2 decoder taps)"),
    ("decoder1_roi_pool", "tap", "roi_pooled_global_features", "SHARED_AXIS",
     "third ROI axis; same allowed contract feature"),

    ("entropy_proxy_mean", "scalar", "probability_entropy_summaries", "DIRECT_EQUIVALENT",
     "the contract's entropy summaries ARE the entropy proxy; the MEAN of that summary is the "
     "frozen statistic"),
    ("frac_prob_within_0p05_of_boundary", "scalar", "predicted_boundary_area_statistics", "DIRECT_EQUIVALENT",
     "boundary-area statistics over the predicted map include the fraction of probability mass "
     "near the boundary; the 0.05 band is the frozen statistic of that allowed feature"),
    ("frac_prob_within_0p02_of_boundary", "scalar", "predicted_boundary_area_statistics", "DIRECT_EQUIVALENT",
     "second deterministic band (0.02) of the same allowed boundary-area statistic"),
    ("mean_boundary_margin", "scalar", "probability_margin_summaries", "DIRECT_EQUIVALENT",
     "the contract's margin summaries ARE the boundary margin; the MEAN is the frozen statistic"),
    ("pred_foreground_fraction", "scalar", "predicted_foreground_fraction", "DIRECT",
     "exact authoritative name match"),
    ("pred_foreground_pixels", "scalar", "predicted_foreground_fraction", "DERIVED",
     "pixels = predicted_foreground_fraction x (H x W); derived from the allowed fraction, "
     "no new information source"),
    ("pred_roi_exists", "scalar", "predicted_component_count", "DERIVED",
     "roi_exists = (predicted_component_count > 0); derived from the allowed component count"),
    ("pred_empty", "scalar", "predicted_component_count", "DERIVED",
     "pred_empty = (predicted_component_count == 0); the exact complement of roi_exists"),
    ("predicted_roi_area_fraction", "scalar", "predicted_roi_fraction", "DIRECT",
     "exact authoritative match (ROI area / image area)"),
    ("predicted_roi_side", "scalar", "predicted_bbox_width_height", "DERIVED",
     "roi_side = max(bbox_width, bbox_height) from the allowed bbox geometry feature"),

    ("task_id_embedding", "task", "allowed_task_domain_embedding", "DIRECT",
     "exact authoritative match; 4 tasks -> embedding dim 16"),
]

for r in MAPPING:
    req, group, feat, kind, deriv = r
    if kind not in ("DERIVED",):
        assert feat in allowed_names, f"MAPPING NOT IN ALLOWED CONTRACT: {feat}"
assert "predicted_foreground_fraction" in allowed_names
assert "predicted_component_count" in allowed_names
assert "predicted_roi_fraction" in allowed_names
assert "predicted_bbox_width_height" in allowed_names
assert "allowed_task_domain_embedding" in allowed_names

FS = TAB / "phase24_router_primary_feature_set.csv"
with FS.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["requested_literal", "group", "contract_feature", "mapping_kind",
                "uses_GT", "available_pre_refinement", "inference_available",
                "resource_cost_enters_delta_hat", "derivation"])
    for req, group, feat, kind, deriv in MAPPING:
        c = by_name.get(feat)
        w.writerow([req, group, feat, kind,
                    c["uses_GT"] if c else "false",
                    c["available_pre_refinement"] if c else "true",
                    c["inference_available"] if c else "true",
                    "false", deriv])

# ---------------------------------------------------------------------------
# module / envelope table
# ---------------------------------------------------------------------------
MOD = TAB / "phase24_spec_module_envelope.csv"
with MOD.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["module", "name", "declared_envelope", "active_envelope",
                "closed_form_params", "within_hard_ceiling", "measured", "note"])
    w.writerow(["R_psi", "BARRRegionalRefinerV1",
                "[16,32,64,128,192] one block/stage", "[16,32,64,96,128] one block/stage",
                "1276401", "true", "false",
                "declared channels exceed 2.0M ceiling; deterministic pre-declared reduction applied"])
    w.writerow(["B_phi", "BARRBenefitRouterV1",
                "hidden [128,64]", "hidden [128,64]",
                "36353", "true", "false",
                "well within 250k ceiling; no reduction required"])
    w.writerow(["S_omega", "BARRPostSafetyV1",
                "input->32->16->1", "input->32->16->1",
                "closed_form_not_frozen_here", "true", "false",
                "post-refinement extension; no second encoder"])
    w.writerow(["G", "Frozen Global MedFiLM (Phase 21)",
                "3523001", "3523001", "3523001", "n/a", "true",
                "frozen anchor; measured in Phase 21"])

# ---------------------------------------------------------------------------
# OOF gain schema (SCHEMA ONLY)
# ---------------------------------------------------------------------------
SCHEMA = TAB / "phase25_future_oof_gain_schema.csv"
with SCHEMA.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["column", "dtype", "role", "uses_GT", "available_pre_refinement",
                "notes"])
    w.writerow(["sample_id", "str", "key", "false", "true", "stable manifest id"])
    w.writerow(["dataset", "str", "stratum", "false", "true", "BUSI/ISIC/KUB/KVASIR"])
    w.writerow(["task_id", "int", "conditioning", "false", "true", "0..3"])
    w.writerow(["oof_fold", "int", "provenance", "false", "true", "0,1,2"])
    w.writerow(["action_available", "bool", "filter", "false", "true",
                "false => ACTION_UNAVAILABLE_GLOBAL_EMPTY, excluded from regression rows"])
    w.writerow(["dice_global", "float", "DERIVED_LABEL_COMPONENT", "true", "false",
                "Dice(G_i, y_i); label side"])
    w.writerow(["dice_refined_fused", "float", "DERIVED_LABEL_COMPONENT", "true", "false",
                "Dice(R_i, y_i); requires refinement to have run"])
    w.writerow(["delta_dice", "float", "TARGET", "true", "false",
                "dice_refined_fused - dice_global; the OOF regression target"])
    w.writerow(["refiner_checkpoint_sha256", "str", "provenance", "false", "true",
                "frozen checkpoint used for this OOF fold"])
    w.writerow(["refiner_best_epoch", "int", "provenance", "false", "true",
                "used for the median-epoch final refit rule"])
    w.writerow(["roi_crop_side_pixels", "int", "provenance", "false", "true",
                "frozen 1.50x / 256 geometry"])

print("wrote phase24_router_primary_feature_set.csv ("
      f"{len(MAPPING)} rows)")
print("  mappings by kind:",
      {k: sum(1 for m in MAPPING if m[3] == k) for k in {m[3] for m in MAPPING}})
print("wrote phase24_spec_module_envelope.csv (4 rows)")
print("wrote phase25_future_oof_gain_schema.csv (11 cols, SCHEMA ONLY, 0 data rows)")
print()
print("  all non-DERIVED mappings resolve to an ALLOWED contract feature: PASS")
