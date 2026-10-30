#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 36 — STATIC PREFLIGHT (no execution).

Emits reports/audits/phase36_robustness_static_preflight_v1_0.json.

Verifies: Phase35 closure exact; Phase36 not previously started; TEST and
ROUTER_HOLDOUT unreachable; no training/optimizer; all four components frozen;
A8/C9 unchanged; image & proposal registries exact; metrics exact; noise seeds
exact; no outcome-selected perturbations; claim boundary exact; science gate
fail-closed; smoke gate separate; source has no import-time model execution.

Model-free. NO torch model construction; NO data read.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase36_robustness_common_v1_0 as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
CHECKS = []


def chk(cid, desc, ok, detail=""):
    CHECKS.append({"id": cid, "desc": desc, "pass": bool(ok), "detail": detail})


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def strip_py(src: str) -> str:
    src = re.sub(r'"""(?:.|\n)*?"""', "", src)
    src = re.sub(r"'''(?:.|\n)*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    return src


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    # --- Phase35 closure authority exact -------------------------------------
    closure_exp = {
        "reports/audits/phase35_canonical_closure_v1_0a.json":
            "7720c1d292292a8a5ea50311674a834e906633f7f168217c2853018703eb7df1",
        "reports/audits/phase35_canonical_closure_final_check_v1_0a.json":
            "7c12f8aac65e9a4acd9ed528ba391f82b9aa65533fc97c7e4a2d9ce774bb5c4d",
        "reports/audits/phase35_canonical_closure_terminal_v1_0a.json":
            "6e343b7f433bbc8a43b3d746b2affd2bbc15ecdaeb9491cdc83e4d02f3d4047d",
    }
    closure_ok = all(sha(ROOT / p) == e for p, e in closure_exp.items())
    chk("01", "Phase35 canonical closure hashes exact (3/3)", closure_ok)

    term = json.loads((AUD / "phase35_canonical_closure_terminal_v1_0a.json").read_text("utf-8"))
    chk("02", "Phase35 == COMPLETE_CANONICAL",
        term["classification"] == "COMPLETE_CANONICAL")
    chk("03", "Phase36 == ELIGIBLE_NOT_STARTED at entry",
        term["phase36_eligibility"] == "ELIGIBLE_NOT_STARTED"
        and term["phase36_started"] is False)
    chk("04", "TEST == LOCKED_UNTIL_PHASE39 at entry",
        term["test_state"] == "LOCKED_UNTIL_PHASE39")

    # --- Phase36 not previously started -------------------------------------
    prior = list(AUD.glob("phase36_*_execution*.json")) + \
            list(AUD.glob("phase36_robustness_smoke*.json"))
    chk("05", "Phase36 not previously started (no prior execution/smoke artifacts)",
        len(prior) == 0, f"prior={[p.name for p in prior]}")

    # --- TEST / ROUTER_HOLDOUT unreachable ----------------------------------
    chk("06", "TEST and ROUTER_HOLDOUT in MUST_NOT_READ; zero declared rows",
        "TEST" in C.MUST_NOT_READ and "ROUTER_HOLDOUT" in C.MUST_NOT_READ
        and C.TEST_ROWS == 0 and C.ROUTER_HOLDOUT_ROWS == 0)

    # --- no training / optimizer --------------------------------------------
    exec_src = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_0.py").read_text("utf-8")
    exec_code = strip_py(exec_src)
    # detect actual optimizer/training CALL patterns, not innocent counter names
    bad_training = [t for t in ["torch.optim", "optim.Adam", "optim.SGD",
                                "Adam(", "SGD(", ".backward()", "optimizer.step",
                                "optimizer.zero_grad", "requires_grad_(True)"]
                    if t in exec_code]
    chk("07", "execution source performs no training / no optimizer step",
        not bad_training, f"found={bad_training}")

    # --- all four components frozen -----------------------------------------
    comp_ok = all(C.COMPONENTS[c]["source_sha256"] and C.COMPONENTS[c]["checkpoint_sha256"]
                  for c in ("G", "B_phi", "R_psi", "S_omega"))
    comp_files_ok = all((ROOT / C.COMPONENTS[c]["checkpoint_path"]).exists()
                        and sha(ROOT / C.COMPONENTS[c]["checkpoint_path"]) ==
                        C.COMPONENTS[c]["checkpoint_sha256"]
                        for c in C.COMPONENTS)
    chk("08", "all four components have frozen source+checkpoint hashes", comp_ok)
    chk("09", "all four component checkpoints present and hash-match", comp_files_ok)

    # --- A8/C9 unchanged -----------------------------------------------------
    chk("10", "A8/C9 policy bound, budget 0.25, no retraining/threshold change",
        C.A8_C9_POLICY["runtime_policy"] == "A8_C9"
        and C.A8_C9_POLICY["nominal_budget"] == 0.25
        and C.A8_C9_POLICY["joint_retraining"] is False
        and C.A8_C9_POLICY["threshold_modification"] is False)
    chk("11", "canonical thresholds unchanged (0.50 seg / 0.30 roi)",
        C.T_SEGMENTATION_OUTPUT == 0.50 and C.T_ROI_PROPOSAL == 0.30
        and C.PROPOSAL_THRESHOLD == 0.30)

    # --- image perturbation registry exact ----------------------------------
    exp_img = ["CLEAN", "BRIGHTNESS_NEG", "BRIGHTNESS_POS", "CONTRAST_LOW",
               "CONTRAST_HIGH", "GAMMA_LOW", "GAMMA_HIGH", "GAUSSIAN_NOISE_LOW",
               "GAUSSIAN_NOISE_HIGH", "GAUSSIAN_BLUR_LOW", "GAUSSIAN_BLUR_HIGH",
               "RESOLUTION_075", "RESOLUTION_050"]
    chk("12", "image perturbation registry exact (13 conditions)",
        C.image_condition_ids() == exp_img, f"got={C.image_condition_ids()}")
    chk("13", "image registry unique & no chaining",
        C.registries_unique() and C.assert_no_chaining())
    chk("14", "no jpeg/color-space/rotation/crop/random augmentation/adversarial",
        C.FORBIDDEN_PERTURBATIONS and all(
            not any(f.replace("_", "") in c.replace("_", "").lower()
                    for c in C.image_condition_ids())
            for f in C.FORBIDDEN_PERTURBATIONS))

    # --- proposal perturbation registry exact -------------------------------
    exp_prop = ["PROPOSAL_CLEAN", "SHIFT_LEFT_10", "SHIFT_RIGHT_10",
                "SHIFT_UP_10", "SHIFT_DOWN_10", "SCALE_085", "SCALE_115"]
    chk("15", "proposal perturbation registry exact (7 conditions)",
        C.proposal_condition_ids() == exp_prop, f"got={C.proposal_condition_ids()}")
    chk("16", "empty proposal handled as NOT_APPLICABLE_EMPTY_PROPOSAL; no outcome replacement",
        C.EMPTY_PROPOSAL_HANDLING == "NOT_APPLICABLE_EMPTY_PROPOSAL"
        and C.NO_OUTCOME_DEPENDENT_REPLACEMENT is True)

    # --- metrics exact -------------------------------------------------------
    chk("17", "metric contract exact (paired_delta_Dice primary; Dice bound)",
        C.PRIMARY_METRIC == "paired_delta_Dice"
        and C.PRIMARY_METRIC_DEF == "Dice_perturbed - Dice_clean")
    chk("18", "IoU and HD95 bound before execution",
        C.SECONDARY_METRICS["iou"]["bound"] and C.SECONDARY_METRICS["hd95"]["bound"])
    chk("19", "Dice impl + empty-mask policy bound with exact hashes",
        C.DICE_IMPL_SHA == sha(ROOT / C.DICE_IMPL_PATH)
        and C.EMPTY_MASK_POLICY_SHA == sha(ROOT / C.EMPTY_MASK_POLICY))

    # --- noise seeds exact ---------------------------------------------------
    seeds = set()
    for cid in ("GAUSSIAN_NOISE_LOW", "GAUSSIAN_NOISE_HIGH"):
        seeds |= set(C.IMAGE_CONDITIONS[cid]["base_seeds"])
    chk("20", "noise seeds exactly {42,123,3407}", seeds == {42, 123, 3407})
    chk("21", "noise seed derivation rule exact",
        C.NOISE_SEED_RULE == 'SHA256("phase36|gaussian_noise|<base_seed>|<sample_id>")')
    chk("22", "no best-seed selection; per-seed then arithmetic mean",
        C.BEST_SEED_SELECTION is False)

    # --- no outcome-selected perturbations ----------------------------------
    chk("23", "no outcome-selected perturbation (frozen before execution)",
        C.NO_POST_HOC_SET_EXPANSION is True
        and C.EXAMPLE_VIZ_MEMBERSHIP_FROZEN_BEFORE_OUTPUTS is True
        and C.OUTCOME_SELECTED_GALLERY_REQUIRED is False)

    # --- claim boundary exact ------------------------------------------------
    chk("24", "claim boundary exact (evidence class + NOT list)",
        C.EVIDENCE_CLASS == "DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE"
        and "clinical robustness" in C.CLAIM_BOUNDARY_NOT
        and "adversarial robustness" in C.CLAIM_BOUNDARY_NOT
        and "external generalization" in C.CLAIM_BOUNDARY_NOT
        and "deployment reliability proof" in C.CLAIM_BOUNDARY_NOT)

    # --- gates ---------------------------------------------------------------
    # science gate fail-closed: inspect exec source for the gate pattern
    chk("25", "science gate fail-closed unless PHASE36_EXECUTE == '1'",
        'GATE_ENV' in exec_code and '!= "1"' in exec_code
        and "return 2" in exec_code)
    chk("26", "smoke gate separate (PHASE36_SMOKE_EXECUTE)",
        C.SMOKE_GATE_ENV == "PHASE36_SMOKE_EXECUTE"
        and C.SMOKE_GATE_ENV != C.GATE_ENV
        and "SMOKE_GATE_ENV" in exec_code)

    # --- source performs no import-time model execution ---------------------
    for name in ["phase36_robustness_common_v1_0.py",
                 "phase36_robustness_execution_v1_0.py",
                 "phase36_robustness_preflight_v1_0.py"]:
        src = (ROOT / "scripts/analysis" / name).read_text("utf-8")
        code = strip_py(src)
        # no top-level torch import; torch import only allowed inside functions
        toplevel_torch = re.search(r"(?m)^import torch", code) or \
                         re.search(r"(?m)^from torch", code)
        chk(f"27{name[-6:-3]}", f"{name}: no import-time torch / model execution",
            toplevel_torch is None
            and "load_state_dict" not in code.split("def ")[0])

    # --- KUB reporting-only -------------------------------------------------
    chk("31", "KUB subgroup metadata is REPORTING_ONLY (never classes/task ids)",
        C.KUB_REPORTING_ONLY and C.DOMAIN_TASK_ID["KUB"] == 3
        and C.KUB_SUBGROUPS == ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"])

    # --- population contract -------------------------------------------------
    chk("32", "population VAL808 only; 808 rows; four domains; 0 holdout/test",
        C.POPULATION_NAME == "VAL808" and C.POPULATION_N == 808
        and set(C.DOMAINS) == {"ISIC", "BUSI", "KVASIR", "KUB"}
        and sum(C.DOMAIN_COUNTS.values()) == 808
        and C.ROUTER_HOLDOUT_ROWS == 0 and C.TEST_ROWS == 0)
    chk("33", "VAL manifest authority hash exact",
        C.VAL_MANIFEST_SHA == sha(ROOT / C.VAL_MANIFEST))

    # --- clean reference ----------------------------------------------------
    cr_ok = all(sha(ROOT / v["path"]) == v["sha256"] for v in C.CLEAN_REFERENCE.values())
    chk("34", "clean reference authority present and hash-exact",
        cr_ok and C.CLEAN_REFERENCE_COMPLETE is True)

    # --- figures / tables ----------------------------------------------------
    chk("35", "figure contract R1-R5 frozen",
        list(C.FIGURES.keys()) == ["R1", "R2", "R3", "R4", "R5"])
    chk("36", "table contract frozen (9 tables incl. KUB conditional)",
        len(C.TABLES) == 9 and "phase36_kub_subgroup_robustness.csv" in C.TABLES)

    # --- state machine -------------------------------------------------------
    chk("37", "frozen state machine exact",
        C.STATE_MACHINE[0] == "G" and "B_phi" in C.STATE_MACHINE
        and "S_omega" in C.STATE_MACHINE
        and C.ROUTE_STATES == ["SKIP", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"])

    passed = sum(1 for c in CHECKS if c["pass"])
    total = len(CHECKS)
    art = {
        "artifact": "phase36_robustness_static_preflight_v1_0",
        "section": "\u00a7R",
        "phase": 36,
        "method": C.METHOD,
        "revision": C.REVISION,
        "preflight_class": "STATIC_NO_EXECUTION",
        "no_execution": True,
        "torch_imported": False,
        "source_hashes": {
            "common": sha(ROOT / "scripts/analysis/phase36_robustness_common_v1_0.py"),
            "execution": sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_0.py"),
            "preflight": sha(ROOT / "scripts/analysis/phase36_robustness_preflight_v1_0.py"),
            "unit": sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_0.py"),
        },
        "checks": CHECKS,
        "total_checks": total,
        "passed": passed,
        "failed": total - passed,
        "all_pass": passed == total,
        "generated_utc": now(),
    }
    out = AUD / "phase36_robustness_static_preflight_v1_0.json"
    out.write_text(json.dumps(art, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": total, "failed": total - passed,
                      "sha256": sha(out)}, indent=1))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
