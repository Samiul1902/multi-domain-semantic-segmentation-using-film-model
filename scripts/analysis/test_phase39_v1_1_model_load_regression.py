"""Phase39 v1.1 model-load regression (Task 6) — no TEST access.

Reproduces the v1.0 D98 mutation (NameError: FEATURE_DIM) and demonstrates the
v1.1 loader closes it. Constructs + strict-loads all four frozen components on
CPU and verifies parameter counts and key sets. Opens NO TEST data.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
A = ROOT / "reports" / "audits"

R = {"checks": {}, "notes": []}


def check(name, ok, note=""):
    R["checks"][name] = bool(ok)
    if not ok:
        R["notes"].append(f"FAIL {name}: {note}")


# --- A. reproduce v1.0 D98 mutation ---
import scripts.analysis.phase39_final_test_model_loader_v1_0 as L0
v1_0_router_ok = v1_0_somega_err = None
try:
    L0.load_router()
    v1_0_router_ok = True
except Exception as e:  # noqa: BLE001
    v1_0_router_ok = False
try:
    L0.load_somega()
    v1_0_somega_err = None
except Exception as e:  # noqa: BLE001
    v1_0_somega_err = f"{type(e).__name__}: {e}"
check("v1_0_router_constructs", v1_0_router_ok)
check("v1_0_somega_reproduces_FeatureDim_NameError",
      v1_0_somega_err is not None and "FEATURE_DIM" in (v1_0_somega_err or ""), v1_0_somega_err)

# --- B. v1.1 closes the defect ---
import scripts.analysis.phase39_final_test_model_loader_v1_1 as L1
v1_1_router_ok = v1_1_somega_ok = False
try:
    L1.load_router(); v1_1_router_ok = True
except Exception:  # noqa: BLE001
    pass
try:
    L1.load_somega(); v1_1_somega_ok = True
except Exception:  # noqa: BLE001
    pass
check("v1_1_router_constructs", v1_1_router_ok)
check("v1_1_somega_constructs", v1_1_somega_ok)

# --- C. full four-component construct + strict load (CPU, no TEST) ---
models = device = audit = None
try:
    models, device, audit = L1.build_all_models(require_cuda=False)
    check("all_four_components_construct", True)
except Exception as e:  # noqa: BLE001
    check("all_four_components_construct", False, repr(e))
    print(traceback.format_exc())

EXPECTED = {"G": 3523001, "B_phi": 36801, "R_psi": 1276401, "S_omega": 1217}
if audit:
    for name, exp in EXPECTED.items():
        check(f"param_count_{name}_{exp}", audit[name]["parameter_count"] == exp,
              f"got {audit[name]['parameter_count']}")
        check(f"zero_missing_keys_{name}", len(audit[name]["missing_keys"]) == 0)
        check(f"zero_unexpected_keys_{name}", len(audit[name]["unexpected_keys"]) == 0)
        check(f"checkpoint_sha_{name}", audit[name]["checkpoint_sha256"] == audit[name]["checkpoint_sha256_expected"])
        check(f"weights_finite_{name}", audit[name]["all_weights_finite"])
    total = sum(audit[n]["parameter_count"] for n in EXPECTED)
    check("total_parameters_4837420", total == 4837420, f"got {total}")

# --- D. no TEST path opened ---
import builtins
opened = []
_real_open = builtins.open
def _spy(file, *a, **k):
    s = str(file).replace("\\", "/").lower()
    if "test" in s and s.endswith((".csv", ".png", ".jpg", ".npy")):
        opened.append(str(file))
    return _real_open(file, *a, **k)
builtins.open = _spy
try:
    if models is None:
        L1.build_all_models(require_cuda=False)
finally:
    builtins.open = _real_open
check("no_test_data_opened", len(opened) == 0, str(opened[:5]))

R["v1_0_mutation_reproduction"] = v1_0_somega_err
R["expected_param_counts"] = EXPECTED
n_pass = sum(1 for v in R["checks"].values() if v)
R["n_pass"] = n_pass
R["n_total"] = len(R["checks"])
R["all_pass"] = n_pass == len(R["checks"])
(A / "phase39_v1_1_model_load_regression_report.json").write_text(
    json.dumps({"classification": "PHASE39_V1_1_MODEL_LOAD_REGRESSION_REPORT",
                "phase": 39, "test_reads": 0, **R}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"MODEL-LOAD REGRESSION: {n_pass}/{R['n_total']} pass | all_pass={R['all_pass']}")
for k, v in R["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'} {k}")
for n in R["notes"]:
    print("  ", n)
sys.exit(0 if R["all_pass"] else 1)
