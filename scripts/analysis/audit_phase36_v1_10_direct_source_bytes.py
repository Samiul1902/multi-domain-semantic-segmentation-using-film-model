#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.10 — DIRECT SOURCE-BYTE AUDIT (READ-ONLY).

Because the v1.10 revision repairs DEFECTIVE UNIT ASSERTIONS only, the
execution subject must remain byte-identical to the frozen v1.9 source.  This
audit inspects the ACTUAL bytes (not comments-only trust):

  1. the execution subject SHA-256 equals the frozen v1.9 SHA;
  2. the four v1.9 execution invariants that D26/D27/D28 assert over are
     present in the actual source bytes (provenance derivation, exclusive
     create, exact 14-path dep set, four hd95 call sites);
  3. the v1.10 unit suite reads exactly that execution source;
  4. no smoke / science artifact exists (nothing executed).

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
UNIT = ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"
NC = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_10.py"

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name):
    return ast.get_source_segment(SRC, FUNCS[name]) if name in FUNCS else ""


items = []


def item(key, ok, evidence=None):
    items.append({"item": key, "pass": bool(ok), "evidence": evidence})


# ---- identity / byte-preservation -------------------------------------------- #
item("v1_9_execution_subject_sha256", sha(EXEC) == FROZEN_V1_9_EXEC_SHA,
     {"expected": FROZEN_V1_9_EXEC_SHA, "observed": sha(EXEC)})
item("v1_9_unit_history_sha256", sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py")
     == FROZEN_V1_9_UNIT_SHA,
     {"expected": FROZEN_V1_9_UNIT_SHA})
item("v1_10_execution_subject_is_v1_9_bytes", sha(EXEC) == FROZEN_V1_9_EXEC_SHA)
item("ast_parse_success", True)
item("line_count", True, len(SRC.splitlines()))

# ---- D26 invariants present in the ACTUAL bytes ------------------------------ #
prov = None
for n in ast.walk(FUNCS["run_smoke"]) if "run_smoke" in FUNCS else []:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "attempt_provenance" \
                    and isinstance(n.value, ast.Dict):
                prov = n.value
prov_val = None
if prov is not None:
    for k, v in zip(prov.keys, prov.values):
        if isinstance(k, ast.Constant) and k.value == "is_first_write_once":
            prov_val = v
prov_names = {x.id for x in ast.walk(prov_val) if isinstance(x, ast.Name)} \
    if prov_val is not None else set()
item("D26_provenance_is_derived_bool_call",
     isinstance(prov_val, ast.Call) and isinstance(prov_val.func, ast.Name)
     and prov_val.func.id == "bool"
     and {"_marker_exists", "_marker_sole_and_trueseal"} <= prov_names,
     {"observed_names": sorted(prov_names)})
item("D26_exclusive_create_open_x_present",
     'open(start_marker_path, "x"' in seg("run_smoke"))
item("D26_write_once_flag_not_literal_true",
     '"is_first_write_once": True' not in SRC)
item("D26_binding_consumes_derived",
     'bool(attempt_provenance["is_first_write_once"])' in SRC)

# ---- D27 invariants: exact 14-path dependency set ----------------------------- #
deps = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_DEPENDENCIES" \
                    and isinstance(n.value, ast.Dict):
                deps = n.value
dep_paths = {k.value for k in deps.keys} if deps is not None else set()
item("D27_exact_14_transitive_dependencies", len(dep_paths) == 14,
     {"observed": len(dep_paths)})
item("D27_expected_14_paths_exact_match",
     dep_paths == {
         "scripts/analysis/phase36_robustness_common_v1_1.py",
         "scripts/analysis/train_phase25d_router.py",
         "scripts/analysis/phase25f_execution_common.py",
         "scripts/analysis/phase25f_post_safety_features.py",
         "src/features/barr_pre_refinement_features.py",
         "src/data/barr_roi.py",
         "src/models/film/global_medfilm.py",
         "src/models/barr/regional_refiner.py",
         "src/models/barr/ra_medfilm_barr.py",
         "src/utils/device.py",
         "src/metrics/evaluation_metrics.py",
         "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json",
         "reports/tables/phase25d_final_normalization_stats.csv",
         "reports/tables/phase25f_final_normalization_stats.csv",
     }, {"observed": sorted(dep_paths)})

# ---- D28 invariants: four ACTUAL hd95 call sites ----------------------------- #
hd_calls = [n for n in ast.walk(FUNCS["run_smoke"])
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_hd95_case_exact"]
item("D28_four_actual_hd95_call_sites", len(hd_calls) == 4,
     {"n": len(hd_calls)})


def _exp(call):
    ref = None
    if call.args and isinstance(call.args[0], ast.Subscript) \
            and isinstance(call.args[0].slice, ast.Constant):
        ref = call.args[0].slice.value
    ev = er = None
    for kw in call.keywords:
        if kw.arg == "expect_valid" and isinstance(kw.value, ast.Constant):
            ev = kw.value.value
        if kw.arg == "expect_reason" and isinstance(kw.value, ast.Constant):
            er = kw.value.value
    return ref, ev, er


observed = {_exp(c) for c in hd_calls}
item("D28_four_hd95_call_semantics_exact",
     observed == {("nonempty_nonempty", True, ""),
                 ("empty_prediction_nonempty_gt", False, "empty_prediction"),
                 ("nonempty_prediction_empty_gt", False, "empty_ground_truth"),
                 ("empty_empty", False, "both_empty")},
     {"observed": sorted(str(x) for x in observed)})

# ---- v1.10 unit suite binds the exact execution source ----------------------- #
u_src = UNIT.read_text(encoding="utf-8")
item("unit_reads_v1_9_execution_source",
     "phase36_robustness_execution_v1_9.py" in u_src)
item("unit_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_robustness_unit_v1_10.json").read_text(
         encoding="utf-8"))["all_pass"])
item("negative_controls_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_v1_10_negative_controls.json").read_text(
         encoding="utf-8"))["all_pass"])

# ---- nothing executed -------------------------------------------------------- #
item("no_smoke_or_science_artifact_written",
     not (ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json").exists()
     and not (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json").exists()
     and not (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json").exists()
     and not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_9.json").exists())
item("no_v1_10_smoke_or_science_artifact_written",
     not (ROOT / "reports/audits/phase36_robustness_smoke_v1_10.json").exists()
     and not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_10.json").exists())

passed = sum(1 for i in items if i["pass"])
total = len(items)
report = {
    "artifact": "phase36_v1_10_direct_source_byte_audit",
    "phase": 36,
    "section": "§M",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "DIRECT_SOURCE_BYTE_AUDIT",
    "read_only": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "execution_sha256": sha(EXEC),
    "n_declared_check_ids": None,
    "items": items,
    "passed": passed,
    "total": total,
    "verdict": ("PASS" if passed == total else "FAIL"),
}
out = ROOT / "reports/audits/phase36_v1_10_direct_source_byte_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "verdict": report["verdict"],
                  "execution_sha256": report["execution_sha256"]}, indent=1))
for i in items:
    if not i["pass"]:
        print("FAIL:", i["item"], json.dumps(i.get("evidence"), default=str))
raise SystemExit(0 if passed == total else 1)
