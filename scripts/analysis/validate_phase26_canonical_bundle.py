"""Phase26 canonical bundle validator (standalone, §24).

Verifies the frozen ``artifacts/phase26_ra_medfilm_barr_bundle_v1_0`` bundle is
internally consistent and that its bindings match the physical frozen artifacts.

This validator MUST NOT access ROUTER_HOLDOUT, VAL808 or TEST.

Usage:
    D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/validate_phase26_canonical_bundle.py
Exit code 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
BUNDLE = ROOT / "artifacts" / "phase26_ra_medfilm_barr_bundle_v1_0"

FORBIDDEN_TOKENS = ("phase4_v3/test", "manifests/test", "test_split",
                    "load_test", "read_test", "test_image", "test_mask",
                    "holdout_image", "holdout_mask", "holdout_score",
                    "holdout_prediction", "val808_image", "val808_mask")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load(name: str):
    return json.loads((BUNDLE / name).read_text(encoding="utf-8"))


def scan_forbidden(text: str) -> list:
    low = text.lower()
    return [t for t in FORBIDDEN_TOKENS if t in low]


def main() -> int:
    checks = {}

    m = load("canonical_bundle_manifest.json")
    inv = load("component_inventory.json")
    tc = load("threshold_contract.json")
    fc = load("feature_contract.json")
    sm = load("state_machine_contract.json")

    # 1. all referenced files exist + SHAs match
    ref_ok = True
    for group in ("components", "normalizations", "schemas"):
        for name, b in m[group].items():
            p = ROOT / b["path"]
            if not p.exists():
                ref_ok = False
                continue
            if b.get("expected_sha256") and sha256_file(p) != b["expected_sha256"]:
                ref_ok = False
    checks["all_referenced_files_exist_and_shas_match"] = ref_ok

    # 2. thresholds parse exactly
    try:
        ok = (Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["resource_utility_threshold_exact"])
              == Fraction(-5003565381643716252018011, 205414980000000000000000000))
        ok = ok and (Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["raw_threshold_exact"])
                     == Fraction(24796109646558761, 20000000000000000000))
        ok = ok and (Fraction(m["A_OOF_SCIENTIFIC_EVIDENCE"]["resource_threshold_exact"])
                     == Fraction(-2326256430798223, 102707490000000000))
    except Exception:  # noqa: BLE001
        ok = False
    checks["all_thresholds_parse_exactly"] = ok

    # 3. runtime authority uniqueness
    a = m["A_OOF_SCIENTIFIC_EVIDENCE"]["runtime_authority"]
    b = m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["runtime_authority"]
    checks["oof_runtime_authority_false"] = a is False
    checks["final_router_runtime_authority_true"] = b is True
    checks["runtime_authority_unique"] = (int(a) + int(b)) == 1

    # 4. lambda / cost exact
    try:
        lam = Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["lambda"])
        cst = Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["normalized_action_cost_exact"])
        lc = Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["lambda_C_exact"])
        raw = Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["raw_threshold_exact"])
        util = Fraction(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["resource_utility_threshold_exact"])
        checks["lambda_cost_exact"] = (lc == lam * cst) and (util == raw - lam * cst)
    except Exception:  # noqa: BLE001
        checks["lambda_cost_exact"] = False

    # 5. component identities exact
    checks["component_identities_exact"] = (
        inv["components"][0]["checkpoint_sha256"]
        == "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
        and any(c["checkpoint_sha256"]
                == "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
                for c in inv["components"])
        and any(c["checkpoint_sha256"]
                == "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"
                for c in inv["components"])
        and any(c["checkpoint_sha256"]
                == "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"
                for c in inv["components"]))

    # 6. normalization identities + schemas exact
    checks["normalization_identities_exact"] = (
        m["normalizations"]["router_normalization"]["expected_sha256"]
        == "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb")
    checks["schemas_exact"] = (
        m["schemas"]["router_schema"]["expected_sha256"]
        == "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"
        and fc["router_feature"]["b_phi_input_dim"] == 218
        and fc["post_safety_feature"]["total_dim"] == 20)

    # 7. state-machine contract exact
    checks["state_machine_contract_exact"] = (
        set(sm["states"]) == {"FORCED_SKIP", "SKIP_GLOBAL",
                              "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"}
        and sm["global_forward_count_per_input"] == 1
        and sm["safety_accept"] == "sigmoid(logit) >= 0.50"
        and sm["final_segmentation"] == "p_final >= 0.50")

    # 8. holdout reservation exact
    checks["holdout_reservation_exact"] = (
        m["locks"]["router_holdout_owner"] == "PHASE30"
        and m["locks"]["router_holdout_state"] == "RESERVED_UNOPENED_FOR_PHASE30"
        and m["locks"]["val808"] == "UNOPENED"
        and m["locks"]["test"] == "LOCKED_UNTIL_PHASE39")

    # 9. no forbidden population tokens anywhere in the bundle
    forbidden_hits = []
    for p in sorted(BUNDLE.iterdir()):
        if p.is_file():
            forbidden_hits += [f"{p.name}:{t}" for t in scan_forbidden(p.read_text(encoding="utf-8"))]
    checks["no_forbidden_population_access"] = len(forbidden_hits) == 0

    # 10. operational threshold selector
    checks["operational_threshold_selector"] = (
        m["operational_threshold"]
        == "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold"
        and tc["operational_threshold_selector"]
        == "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold")

    all_pass = all(checks.values())
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    if forbidden_hits:
        print("  forbidden hits:", forbidden_hits)
    print("VALIDATOR " + ("PASS" if all_pass else "FAIL"))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
