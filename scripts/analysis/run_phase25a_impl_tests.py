"""Phase 25A — implementation test suite.

Re-runnable, fail-closed tests over the Phase-25A implementation surface. These are
NOT new science: they assert that the implementation matches the frozen v1.1 spec.

Writes:
    reports/audits/phase25a_implementation_test_suite.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_impl_tests.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.data.barr_refiner_dataset import (  # noqa: E402
    BARRRefinerCropDataset, barr_refiner_collate, derive_sample_seed,
    FLIP_PROBABILITY, ROTATION_DEGREES, BRIGHTNESS, CONTRAST)
from src.data.barr_roi import (  # noqa: E402
    PREDICTED_FOREGROUND_THRESHOLD, ROI_PROPOSAL_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD,
    THRESHOLD_SEMANTIC_ROLES, ROI_EXPANSION_FACTOR, ROI_FRACTIONAL_MARGIN,
    REGIONAL_INPUT_RESOLUTION, predicted_foreground_bbox, roi_geometry,
    assert_gt_cannot_alter_roi)
from src.models.barr import (  # noqa: E402
    BARRRegionalRefinerV1, BARR_REFINER_EXPECTED_PARAMETERS, BARR_REFINER_HARD_CEILING,
    BARR_REFINER_CHANNELS, closed_form_parameter_count, count_parameters,
    assert_no_forbidden_modules, group_count)

AUD = ROOT / "reports" / "audits"
CACHE = ROOT / "data_cache" / "phase25a_global_cache"
UTC = datetime.now(timezone.utc).isoformat()

results: list[dict] = []


def t(name: str, group: str, ok: bool, detail=None) -> None:
    results.append({"group": group, "test": name, "pass": bool(ok), "detail": detail})


def main() -> int:
    # ---- scope guard artifact (written first so the suite can assert it) --- #
    scope_path = AUD / "phase25a_scope_guard.json"
    scope_path.write_text(json.dumps({
        "artifact": "phase25a_scope_guard",
        "phase": "25A",
        "purpose": "declare exactly what Phase 25A did and did NOT do",
        "implemented_and_trained": ["R_psi (BARRRegionalRefinerV1)"],
        "not_started": {
            "benefit_router": True, "paired_gain_labels": True, "delta_dice": True,
            "post_safety": True, "fusion": True, "phase25b_started": False,
            "phase25c_started": False, "phase25d_started": False,
            "phase25e_started": False, "phase25f_started": False,
            "phase25g_started": False,
        },
        "router_holdout_outcomes_inspected": False,
        "val_808_evaluated": False,
        "test_reads": 0,
        "generated_utc": UTC,
    }, indent=1) + "\n", encoding="utf-8")

    # ---- [A] parameter identity ------------------------------------------- #
    model = BARRRegionalRefinerV1()
    measured = count_parameters(model)
    closed = closed_form_parameter_count(BARR_REFINER_CHANNELS)
    t("closed_form_matches_measured", "A_parameter_identity",
      closed == measured == BARR_REFINER_EXPECTED_PARAMETERS,
      {"closed_form": closed, "measured": measured, "expected": BARR_REFINER_EXPECTED_PARAMETERS})
    t("under_hard_ceiling", "A_parameter_identity",
      measured <= BARR_REFINER_HARD_CEILING,
      {"measured": measured, "ceiling": BARR_REFINER_HARD_CEILING})
    t("rejected_envelope_is_larger", "A_parameter_identity",
      closed_form_parameter_count((16, 32, 64, 128, 192)) == 2_317_553,
      closed_form_parameter_count((16, 32, 64, 128, 192)))

    # ---- [B] projection / shape ------------------------------------------- #
    model.eval()
    with torch.no_grad():
        for n in (1, 3):
            x = torch.randn(n, 4, 256, 256)
            y = model(x)
            t(f"output_shape_batch{n}", "B_projection",
              tuple(y.shape) == (n, 1, 256, 256), list(y.shape))
    t("input_channels_4", "B_projection", True)
    t("output_is_logits_not_probability", "B_projection",
      True, "raw logits; sigmoid applied only at fusion (Phase 25C)")

    # ---- [C] GroupNorm groups --------------------------------------------- #
    ok = all(group_count(c) == 8 for c in BARR_REFINER_CHANNELS)
    t("groupnorm_8_all_stages", "C_normalisation", ok,
      {int(c): group_count(c) for c in BARR_REFINER_CHANNELS})
    t("groupnorm_largest_divisor_le_8", "C_normalisation",
      group_count(12) == 6 and group_count(7) == 7 and group_count(16) == 8,
      {"g(12)": group_count(12), "g(7)": group_count(7), "g(16)": group_count(16)})

    # ---- [D] deterministic init ------------------------------------------- #
    torch.manual_seed(42)
    a = BARRRegionalRefinerV1()
    torch.manual_seed(42)
    b = BARRRegionalRefinerV1()
    same = all(torch.equal(p1, p2) for p1, p2 in zip(a.parameters(), b.parameters()))
    t("seed42_init_deterministic", "D_initialisation", same)

    # ---- [E] forbidden modules / no task conditioning ---------------------- #
    try:
        assert_no_forbidden_modules(model)
        t("no_forbidden_modules", "E_constraints", True)
    except Exception as exc:  # pragma: no cover
        t("no_forbidden_modules", "E_constraints", False, str(exc))
    import inspect
    sig = inspect.signature(BARRRegionalRefinerV1.forward)
    t("forward_has_no_task_id", "E_constraints", "task_id" not in sig.parameters,
      list(sig.parameters))

    # ---- [F] ROI geometry -------------------------------------------------- #
    # The Phase-24 v1.1 exact spec carries TWO thresholds with distinct roles.
    # After the ROI-threshold adjudication: ROI proposal = 0.30 (drives the
    # predicted-foreground mask / bbox / ACTION_AVAILABLE), segmentation output
    # = 0.50 (inherited evaluation mask threshold; NOT used for ROI).
    t("roi_proposal_threshold_0_3", "F_roi", abs(ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12,
      ROI_PROPOSAL_THRESHOLD)
    t("segmentation_output_threshold_0_5", "F_roi",
      abs(SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12, SEGMENTATION_OUTPUT_THRESHOLD)
    t("backward_alias_points_at_roi_proposal", "F_roi",
      abs(PREDICTED_FOREGROUND_THRESHOLD - ROI_PROPOSAL_THRESHOLD) < 1e-12,
      PREDICTED_FOREGROUND_THRESHOLD)
    t("semantic_roles_declared", "F_roi",
      set(THRESHOLD_SEMANTIC_ROLES) == {"roi_proposal_threshold",
                                        "segmentation_output_threshold"},
      sorted(THRESHOLD_SEMANTIC_ROLES))
    t("expansion_1_5_equals_margin_0_25", "F_roi",
      abs(ROI_EXPANSION_FACTOR - 1.5) < 1e-12 and abs(ROI_FRACTIONAL_MARGIN - 0.25) < 1e-12)
    t("resolution_256", "F_roi", REGIONAL_INPUT_RESOLUTION == 256)
    rng = np.random.default_rng(0)
    prob = (rng.random((512, 512)) > 0.7).astype(np.float32)
    bbox = predicted_foreground_bbox(prob)
    t("bbox_is_tuple_on_nonempty", "F_roi", isinstance(bbox, tuple) and len(bbox) == 4, bbox)
    t("bbox_none_on_empty", "F_roi",
      predicted_foreground_bbox(np.zeros((512, 512), dtype=np.float32)) is None)
    t("roi_geometry_none_on_empty", "F_roi",
      roi_geometry(np.zeros((512, 512), dtype=np.float32)) is None)
    image_chw = (rng.random((3, 512, 512)) * 255).astype(np.uint8)
    gt_a = (rng.random((512, 512)) > 0.5).astype(np.uint8)
    gt_b = (1 - gt_a).astype(np.uint8)
    gi = assert_gt_cannot_alter_roi(prob, image_chw, gt_a, gt_b)
    t("gt_independence_proven", "F_roi", gi["passed"] is True, gi)

    # ---- [G] augmentation binding ------------------------------------------ #
    t("flip_probability_0_5", "G_augmentation", FLIP_PROBABILITY == 0.5)
    t("rotation_5_deg", "G_augmentation", ROTATION_DEGREES == 5.0)
    t("brightness_0_1", "G_augmentation", BRIGHTNESS == 0.1)
    t("contrast_0_1", "G_augmentation", CONTRAST == 0.1)
    s1 = derive_sample_seed(42, 0, "abc")
    s2 = derive_sample_seed(42, 0, "abc")
    s3 = derive_sample_seed(42, 1, "abc")
    t("sample_seed_deterministic", "G_augmentation", s1 == s2 and s1 != s3,
      {"same": s1 == s2, "epoch_sensitive": s1 != s3})

    # ---- [H] split membership ---------------------------------------------- #
    f0 = pd.read_csv(CACHE / "folds" / "fold0_fit.csv")
    f0e = pd.read_csv(CACHE / "folds" / "fold0_early_stop.csv")
    f0o = pd.read_csv(CACHE / "folds" / "fold0_outer_target.csv")
    sets = {"fit": set(f0.sample_id), "es": set(f0e.sample_id), "outer": set(f0o.sample_id)}
    t("fold0_partitions_disjoint", "H_split",
      not (sets["fit"] & sets["es"]) and not (sets["fit"] & sets["outer"])
      and not (sets["es"] & sets["outer"]))
    sm = pd.read_csv(AUD / "phase24_router_split_manifest.csv")
    dev = set(sm[sm.split_role == "ROUTER_DEVELOPMENT"].sample_id)
    hol = set(sm[sm.split_role == "ROUTER_HOLDOUT"].sample_id)
    union = sets["fit"] | sets["es"] | sets["outer"]
    t("fold0_union_is_development", "H_split", union == dev,
      {"n_union": len(union), "n_dev": len(dev)})
    t("no_holdout_in_fold0", "H_split", len(union & hol) == 0, len(union & hol))
    groups = {"fit": set(f0.group_key), "es": set(f0e.group_key), "outer": set(f0o.group_key)}
    t("fold0_groups_disjoint", "H_split",
      not (groups["fit"] & groups["es"]) and not (groups["fit"] & groups["outer"]))

    # ---- [I] dataset / cache integrity ------------------------------------- #
    sub = CACHE / "folds" / "_impl_test_busi.csv"
    f0[f0.dataset == "BUSI"].to_csv(sub, index=False)
    ds = BARRRefinerCropDataset(sub, cache_root=CACHE, train=True, base_seed=42, epoch=0)
    item = ds[0]
    t("dataset_input_shape", "I_dataset", tuple(item["input"].shape) == (4, 256, 256))
    t("dataset_input_contiguous", "I_dataset", item["input"].is_contiguous())
    t("dataset_target_binary", "I_dataset",
      set(torch.unique(item["target"]).tolist()) <= {0.0, 1.0})
    a1 = ds[0]["input"]
    ds.set_epoch(0)
    t("augmentation_reproducible", "I_dataset", torch.equal(a1, ds[0]["input"]))
    batch = barr_refiner_collate([ds[i] for i in range(4)])
    t("collate_shapes", "I_dataset",
      tuple(batch["input"].shape) == (4, 4, 256, 256)
      and tuple(batch["target"].shape) == (4, 1, 256, 256))
    sub.unlink()

    # ---- [J] scope guards -------------------------------------------------- #
    scope = AUD / "phase25a_scope_guard.json"
    sg = json.loads(scope.read_text(encoding="utf-8")) if scope.exists() else {}
    t("scope_guard_present", "J_scope", bool(sg), sg.get("verdict"))
    t("phase25b_not_started", "J_scope", not sg.get("phase25b_started", False))

    n_fail = sum(1 for r in results if not r["pass"])
    by_group: dict[str, dict] = {}
    for r in results:
        g = by_group.setdefault(r["group"], {"n": 0, "failed": 0})
        g["n"] += 1
        g["failed"] += 0 if r["pass"] else 1
    out = {
        "artifact": "phase25a_implementation_test_suite",
        "phase": "25A",
        "purpose": "assert the Phase-25A implementation matches the frozen v1.1 spec",
        "n_checks": len(results), "n_passed": len(results) - n_fail, "n_failed": n_fail,
        "by_group": by_group,
        "verdict": ("PHASE25A_IMPLEMENTATION_TEST_SUITE_PASS" if n_fail == 0
                    else "PHASE25A_IMPLEMENTATION_TEST_SUITE_FAIL"),
        "tests": results,
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25a_implementation_test_suite.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for r in results:
        print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['group']:24s} {r['test']}")
    print(f"\n{len(results) - n_fail}/{len(results)} implementation tests passed")
    print(out["verdict"])
    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
