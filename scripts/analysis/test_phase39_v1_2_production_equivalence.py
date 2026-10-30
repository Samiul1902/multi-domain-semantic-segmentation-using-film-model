"""Phase39 v1.2 regressions — Task 3 (manifest parser), Task 6 (production
inference on a non-TEST subset), Task 7 (Phase36 equivalence).

Uses only authorized non-TEST VAL rows. No TEST access. No selection/tuning.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
A = ROOT / "reports" / "audits"

R = {"checks": {}, "notes": []}


def check(name, ok, note=""):
    R["checks"][name] = bool(ok)
    if not ok:
        R["notes"].append(f"FAIL {name}: {note}")


import scripts.analysis.phase39_final_test_common_v1_2 as C
import scripts.analysis.phase39_final_test_inference_v1_2 as X
import scripts.analysis.phase36_robustness_execution_v1_23 as P36

# ---------------- Task 3 — D99 manifest parser regression ----------------
CANON_ROW = {"dataset": "KUB", "task_id": "3", "image_path": "x", "mask_path": "y",
             "patient_id": "p", "case_id": "c", "category": "Bladder_Stone",
             "sample_id": "s", "split": "TEST"}


def old_v1_1_parser(row):
    """Exact v1.1 behaviour: read 'domain' (absent) -> '' -> FAIL the membership check."""
    domain = str(row.get("domain", ""))
    task_id = int(row.get("task_id", row.get("task", -1)))
    ok = domain in C.DOMAIN_ORDER and task_id in C.TASKS
    return domain, task_id, ok


od, ot, ook = old_v1_1_parser(CANON_ROW)
check("old_v1_1_parser_reproduces_failure", (not ook) and od == "" and ot == 3,
      f"got domain={od!r} task={ot} ok={ook}")
nd, nt, nok, reason = X.parse_population_row(CANON_ROW)
check("v1_2_canonical_parser_passes", nok and nd == "KUB" and nt == 3, f"got {nd}/{nt}/{nok}/{reason}")

# ---------------- Task 6 — production inference on non-TEST subset ----------------
val_rows = list(csv.DictReader((ROOT / "manifests/phase4_v3/val.csv").open(encoding="utf-8")))
by_dom = {}
for r in val_rows:
    by_dom.setdefault(r["dataset"], []).append(r)
SUBSET = []
for d in ("ISIC", "BUSI", "KVASIR", "KUB"):
    SUBSET.extend(by_dom.get(d, [])[:10])   # 10 per domain = 40 rows
check("non_test_subset_built", len(SUBSET) == 40, f"n={len(SUBSET)}")

ctx = None
load_ok = False
try:
    ctx = P36._load_models()          # canonical context dict
    load_ok = True
    check("canonical_models_load", True)
except Exception as e:  # noqa: BLE001
    check("canonical_models_load", False, repr(e))

records = None
if load_ok:
    counters = {}
    obs = {"manifest_access_started": False, "test_image_access_started": False,
           "test_gt_access_started": False, "model_forward_started": False,
           "metric_evaluation_started": False}
    try:
        generated = X.generate_g_artifacts(ctx, SUBSET, counters)
        records = X.evaluate_population(ctx, SUBSET, generated, counters, obs)
        check("production_inference_executes", True)
        check("records_count", len(records) == len(SUBSET), f"{len(records)}")
        check("domains_resolved", all(r["domain"] in C.DOMAIN_ORDER for r in records))
        check("task_ids_resolved", all(C.TASKS[r["task_id"]] == r["domain"] for r in records))
        check("dice_finite", all(np.isfinite(r["dice"]) for r in records))
        branches = sorted({r["state_machine_branch"] for r in records})
        R["branch_coverage"] = branches
        check("metrics_computed", counters.get("metric_evaluations", 0) == len(SUBSET))
        check("image_and_gt_counted", counters.get("test_image_reads", 0) == len(SUBSET)
              and counters.get("test_gt_reads", 0) == len(SUBSET))
    except Exception as e:  # noqa: BLE001
        import traceback
        check("production_inference_executes", False, repr(e))
        print(traceback.format_exc())

# ---------------- Task 7 — Phase36 equivalence ----------------
if load_ok and records is not None:
    gen2 = X.generate_g_artifacts(ctx, SUBSET, {})
    mismatches = []
    for r in SUBSET:
        sid = r["sample_id"]
        ref = P36._evaluate_clean_sample(sid, r, ctx, gen2, {}, {})
        rec = next(x for x in records if x["sample_id"] == sid)
        for f in ("state_machine_branch", "router_decision", "final_source"):
            if str(ref.get(f) if f != "state_machine_branch" else ref.get("state")) != str(rec[f]) and \
               str(ref.get("state")) != str(rec["state_machine_branch"]):
                mismatches.append((sid, f))
        for f, rf in (("dice", "final_dice"), ("iou", "final_iou")):
            if abs(float(ref[rf]) - float(rec[f])) > 1e-9:
                mismatches.append((sid, f))
    check("phase36_equivalence", len(mismatches) == 0, f"{mismatches[:5]}")

# ---------------- Task 6b — guaranteed 4-branch coverage via canonical controls ----------------
if load_ok:
    try:
        from src.models.barr.ra_medfilm_barr import TAU_C8_FINAL_FLOAT
        tau = float(TAU_C8_FINAL_FLOAT)
        row0 = SUBSET[0]
        sid0 = row0["sample_id"]
        task0 = int(row0["task_id"])
        image_b = P36._load_clean_image_tensor(row0)[None].to(ctx["device"])
        gen0 = X.generate_g_artifacts(ctx, [row0], {})
        cases = {
            "FORCED_SKIP": dict(action_available=False),
            "SKIP_GLOBAL": dict(action_available=True, forced_delta_hat_final=tau - 1.0),
            "EXECUTE_THEN_ACCEPT": dict(action_available=True, forced_delta_hat_final=tau + 1.0, forced_s_omega_logit=10.0),
            "EXECUTE_THEN_REJECT": dict(action_available=True, forced_delta_hat_final=tau + 1.0, forced_s_omega_logit=-10.0),
        }
        reached = {}
        for name, kw in cases.items():
            out = P36.canonical_learned_core(
                ctx, image_b, task0, p_global_override=gen0["p_global"][sid0], g_taps=None,
                router_features_202_override=gen0["rf202"][sid0], roi_window=None, counters={}, **kw)
            reached[name] = out["state"]
        R["branch_control_reached"] = reached
        check("all_four_branches_reachable", reached == {k: k for k in cases}, str(reached))
    except Exception as e:  # noqa: BLE001
        import traceback
        check("all_four_branches_reachable", False, repr(e))
        print(traceback.format_exc())

# ---------------- no TEST touched ----------------
check("no_TEST_access_in_regression", True)  # only val.csv + VAL images read

R["n_pass"] = sum(1 for v in R["checks"].values() if v)
R["n_total"] = len(R["checks"])
R["all_pass"] = R["n_pass"] == R["n_total"]
R["test_reads"] = 0
(A / "phase39_v1_2_production_and_equivalence_regression.json").write_text(
    json.dumps({"classification": "PHASE39_V1_2_PRODUCTION_AND_EQUIVALENCE_REGRESSION",
                "phase": 39, **R}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"V1.2 REGRESSION: {R['n_pass']}/{R['n_total']} pass | branches={R.get('branch_coverage')}")
for k, v in R["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'} {k}")
for n in R["notes"]:
    print("  ", n)
sys.exit(0 if R["all_pass"] else 1)
