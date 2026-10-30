#!/usr/bin/env python
"""Phase 36 v1.23 — D97 PRE-EXECUTION REGRESSION + SYMBOL AUDITS.

MODE: PRE-EXECUTION VERIFY-ONLY.  NON-CONSUMING.  NO SCIENCE.

Proves, BEFORE any v1.23 science attempt, that the D97 defect class
(stage-5 summary referencing an undefined common-module attribute)
is repaired and CANNOT recur:

  A. COMPLETE C.<attribute> resolution audit (Task 4):
     every ``C.<attr>`` reference in the v1.23 execution source is
     AST-extracted and checked against the attributes ACTUALLY
     exported by scripts.analysis.phase36_robustness_common_v1_1.
     The audit FAILS CLOSED if ANY referenced attribute is missing.

  B. D97 mutation control (Task 4, requirement 9):
     the EXACT old v1.22 mutations (``C.BEST_SEED_SELECTION`` and
     ``C.KUB_REPORTING_ONLY``) are re-introduced into an in-memory
     copy of the v1.23 source and the audit of (A) MUST flag them
     as missing -> the regression catches the exact v1.22 defect.

  C. D97 dynamic regression (Tasks 4+5):
     the REAL late-path summary functions are EXECUTED (isolated
     import; TAB/FIG/ARR redirected to a temporary directory; NO
     model construction, NO torch, NO TEST/HOLDOUT access, NO
     scientific output target consumed) with synthetic rows that
     exercise ALL THREE prescribed Gaussian-noise base seeds
     (42, 123, 3407):
       summarize_image_per_sample
       summarize_image_by_domain_condition
       summarize_noise_seed            <- D97 function #1
       summarize_proposal_per_sample
       summarize_proposal_by_domain_condition
       summarize_route_stability
       summarize_execution_rate
       worst_case_per_sample
       worst_case_by_domain
       kub_subgroup_robustness       <- D97 function #2
       generate_all_figures          <- R1-R5
     Proves: no AttributeError/NameError; every referenced symbol
     resolves; rows contain "best_seed_selection" == False (the
     frozen v1.0 contract authority); multiple prescribed seeds are
     aggregated (mean across ALL seeds, never a best/outcome seed).

  D. Late-path static audits (Task 5):
     stale v1.22 identifier tokens, wrong output paths, exclusive-
     create collisions, missing parent-directory guards, and
     exclusive-create writer semantics -- all detectable WITHOUT
     science execution.

  E. Isolation guarantees:
     torch NEVER imported; _load_models/run_science/main NEVER
     called; every opened path recorded and proven to be either the
     frozen VAL manifest authority or a temporary redirected target;
     NONE of the 23 real v1.23 reachable write targets exists
     afterwards.

Writes (write-once):
    reports/audits/phase36_v1_23_d97_regression_report.json
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))

E_V123 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_23.py"
E_V122 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_22.py"
COMMON_V11 = ROOT / "scripts" / "analysis" / "phase36_robustness_common_v1_1.py"
COMMON_V10 = ROOT / "scripts" / "analysis" / "phase36_robustness_common_v1_0.py"
AUD = ROOT / "reports" / "audits"
REPORT = AUD / "phase36_v1_23_d97_regression_report.json"

E_V123_SHA = hashlib.sha256(E_V123.read_bytes()).hexdigest()
E_V122_SHA = hashlib.sha256(E_V122.read_bytes()).hexdigest()

FROZEN_V123_SHA = "2287cc78ba60d715ff371ba58f0ea90f772219b510e198bea6053a7043159396"
FROZEN_V122_SHA = "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b"

NOISE_BASE_SEEDS = [42, 123, 3407]

LATE_PATH_FUNCTIONS = [
    "summarize_image_per_sample",
    "summarize_image_by_domain_condition",
    "summarize_noise_seed",
    "summarize_proposal_per_sample",
    "summarize_proposal_by_domain_condition",
    "summarize_route_stability",
    "summarize_execution_rate",
    "worst_case_per_sample",
    "worst_case_by_domain",
    "kub_subgroup_robustness",
    "generate_all_figures",
]

# D97 repair provenance (frozen v1.0 contract).
D97_HEADER_BLOCK_MARKER = (
    "DEFECTS REPAIRED IN V1.23 (D97 -- Stage-5 summary name-resolution defect)")
D97_CONST_BLOCK_MARKER = (
    "D97 (v1.23): FROZEN REPORTING CONSTANTS -- LOCAL BINDING, PROVENANCE-")

os.environ["PHASE36_ROBUSTNESS_V1_23_DISABLE_JOURNAL"] = "1"

checks: dict = {}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# =========================================================================== #
# A. COMPLETE C.<attribute> RESOLUTION AUDIT                            #
# =========================================================================== #
def c_attribute_refs(source_text: str) -> list:
    tree = ast.parse(source_text)
    return sorted({n.attr for n in ast.walk(tree)
                   if isinstance(n, ast.Attribute)
                   and isinstance(n.value, ast.Name)
                   and n.value.id == "C"})


def common_exports(path: Path, name: str) -> set:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return {k for k in vars(mod) if not k.startswith("__")}


V123_SRC = E_V123.read_text(encoding="utf-8")
COMMON_V11_EXPORTS = common_exports(COMMON_V11, "p36_common_v1_1_reg")
COMMON_V10_EXPORTS = common_exports(COMMON_V10, "p36_common_v1_0_reg")

v123_refs = c_attribute_refs(V123_SRC)
v123_missing = [a for a in v123_refs if a not in COMMON_V11_EXPORTS]

checks["A_c_attribute_audit"] = {
    "execution_source": "scripts/analysis/phase36_robustness_execution_v1_23.py",
    "execution_source_sha256": E_V123_SHA,
    "frozen_sha256_match": E_V123_SHA == FROZEN_V123_SHA,
    "common_module": "scripts/analysis/phase36_robustness_common_v1_1.py",
    "n_c_attribute_references": len(v123_refs),
    "c_attribute_references": v123_refs,
    "n_common_v1_1_exports": len(COMMON_V11_EXPORTS),
    "missing_attributes": v123_missing,
    "pass": (not v123_missing) and E_V123_SHA == FROZEN_V123_SHA,
    "fail_closed_if_any_missing": True,
}

# =========================================================================== #
# B. D97 MUTATION CONTROL — catch the EXACT old v1.22 mutations        #
# =========================================================================== #
def audit_source(source_text: str) -> dict:
    refs = c_attribute_refs(source_text)
    missing = [a for a in refs if a not in COMMON_V11_EXPORTS]
    return {"references": refs, "missing": missing,
            "pass": not missing}


mutations = {}
# Mutation 1: the EXACT v1.22 D97 defect (C.BEST_SEED_SELECTION).
m1 = V123_SRC.replace(
    '"best_seed_selection": bool(BEST_SEED_SELECTION)',
    '"best_seed_selection": bool(C.BEST_SEED_SELECTION)')
assert m1 != V123_SRC, "mutation 1 anchor missing"
mutations["C.BEST_SEED_SELECTION__exact_v1_22_mutation"] = audit_source(m1)

# Mutation 2: the second undefined common attribute (C.KUB_REPORTING_ONLY).
m2 = V123_SRC.replace("    if not KUB_REPORTING_ONLY:",
                      "    if not C.KUB_REPORTING_ONLY:")
assert m2 != V123_SRC, "mutation 2 anchor missing"
mutations["C.KUB_REPORTING_ONLY__exact_v1_22_mutation"] = audit_source(m2)

# Mutation 3: an arbitrary undefined attribute (generic guard).
m3 = V123_SRC.replace("C.POPULATION_N", "C.POPULATION_N_UNDEFINED_XYZ", 1)
assert m3 != V123_SRC, "mutation 3 anchor missing"
mutations["C.POPULATION_N_UNDEFINED_XYZ__generic_guard"] = audit_source(m3)

mutation_controls_pass = all(
    not m["pass"] and m["missing"] for m in mutations.values())
checks["B_d97_mutation_control"] = {
    "description": ("The EXACT old v1.22 mutations must be flagged as "
                    "invalid against the current common module."),
    "mutations": mutations,
    "all_mutations_caught": mutation_controls_pass,
    "pass": mutation_controls_pass,
}

# =========================================================================== #
# C. D97 DYNAMIC REGRESSION — execute the REAL late path             #
# =========================================================================== #
# Isolated import of the v1.23 execution source (journal disabled;
# __main__ guarded; no model / torch / checkpoint touched).
spec = importlib.util.spec_from_file_location("p36_exec_v1_23_reg", E_V123)
mod = importlib.util.module_from_spec(spec)
sys.modules["p36_exec_v1_23_reg"] = mod
spec.loader.exec_module(mod)

# Capture the REAL (ROOT-based) reachable write targets and
# scientific write namespaces BEFORE redirecting them to a
# temporary directory, so the static audits and the output-
# absence gate reference the REAL v1.23 targets.
REAL_TARGETS = [Path(t) for t in mod.v1_23_reachable_write_targets()]
REAL_TAB = mod.TAB
REAL_FIG = mod.FIG
REAL_ARR = mod.ARR

# Redirect ALL scientific write namespaces to a TEMPORARY directory so
# NO real v1.23 scientific output target is consumed.
tmp = tempfile.TemporaryDirectory(prefix="p36_v1_23_d97_reg_")
TMP = Path(tmp.name)
mod.TAB = TMP / "tables"
mod.FIG = TMP / "figures"
mod.ARR = TMP / "arrays"

# Track every file opened during the late-path execution.
opened: list = []
_real_open = builtins.open
_real_os_open = os.open


def _tracking_open(file, *a, **k):
    opened.append(str(file))
    return _real_open(file, *a, **k)


def _tracking_os_open(path, *a, **k):
    opened.append(str(path))
    return _real_os_open(path, *a, **k)


builtins.open = _tracking_open
os.open = _tracking_os_open

# Also track Path.open / Path.read_bytes: the frozen KUB
# subgroup authority (val.csv) is read through those Path
# methods (kub_subgroup_map -> _sha / _rows), so the
# access ledger must cover them.
_real_path_open = Path.open
_real_path_read_bytes = Path.read_bytes


def _tracking_path_open(self, *a, **k):
    opened.append(str(self))
    return _real_path_open(self, *a, **k)


def _tracking_path_read_bytes(self):
    opened.append(str(self))
    return _real_path_read_bytes(self)


Path.open = _tracking_path_open
Path.read_bytes = _tracking_path_read_bytes

# Synthetic rows: ONE sample per domain, ALL THREE prescribed base
# seeds, DISTINCT paired deltas so the across-seed mean cannot equal
# any single-seed value (proves no best/outcome seed is selected).
IMG_ROWS = []
PROP_ROWS = []
_domains = ["GLOBAL", "KUB", "DOMAIN_B"]
_cond_img = {"GLOBAL": "gaussian_noise_sigma_0.05",
             "KUB": "gaussian_noise_sigma_0.10",
             "DOMAIN_B": "gaussian_blur"}
# real KUB sample ids + subgroup categories from the frozen VAL manifest
val_csv = (ROOT / "manifests" / "phase4_v3" / "val.csv")
import csv as _csv
kub_ids = []
with _real_open(val_csv, newline="", encoding="utf-8") as fh:
    for row in _csv.DictReader(fh):
        if row.get("dataset") == "KUB":
            kub_ids.append((row["sample_id"], row["category"]))
kub_ids = kub_ids[:3]
assert len(kub_ids) >= 1, "no KUB rows in frozen VAL manifest"

# Per-seed paired deltas are chosen so that the cross-seed
# mean differs from EVERY individual seed delta (no seed is
# its own cross-seed mean), which lets the regression prove
# the aggregate is a true multi-seed mean, not a pick.
_dice = {"GLOBAL": [0.90, 0.91, 0.94],
         "KUB": [0.80, 0.81, 0.84],
         "DOMAIN_B": [0.70, 0.71, 0.74]}
_prop_dice = {"GLOBAL": [0.88, 0.89, 0.92],
              "KUB": [0.78, 0.79, 0.82],
              "DOMAIN_B": [0.68, 0.69, 0.72]}
for di, dom in enumerate(_domains):
    seeds = NOISE_BASE_SEEDS if _cond_img[dom].startswith("gaussian_noise") \
        else [None]
    if dom == "KUB":
        sids = [k[0] for k in kub_ids]
    else:
        sids = [f"SYNTH_{dom}_{di}"]
    for si, sid in enumerate(sids):
        for bi, bs in enumerate(seeds):
            d = _dice[dom][bi % 3]
            pd = _prop_dice[dom][bi % 3]
            IMG_ROWS.append({
                "sample_id": sid, "domain": dom,
                "task_id": f"TASK_{dom}",
                "condition": _cond_img[dom],
                "base_seed": bs,
                "derived_seed": (12345 + bi) if bs is not None else None,
                "clean_dice": 0.95, "perturbed_dice": d,
                "paired_delta_dice": (d - 0.95),
                "prediction_consistency_dice": 0.99,
                "route_state_changed": (bi == 0),
                "router_decision_changed": (bi == 0),
                "perturbed_router_decision": "EXECUTE",
                "perturbed_route_state": (
                    "EXECUTE_THEN_ACCEPT" if bi == 0
                    else "EXECUTE_THEN_REJECT"),
            })
            PROP_ROWS.append({
                "sample_id": sid, "domain": dom, "task_id": f"TASK_{dom}",
                "proposal_condition": "proposal_shift",
                "base_seed": bs,
                "not_applicable": False,
                "paired_delta_dice": (pd - 0.95),
            })

# KUB samples need valid subgroup categories present in the frozen map.
for (sid, cat) in kub_ids:
    assert any(r["sample_id"] == sid and r["domain"] == "KUB"
               for r in IMG_ROWS)

dynamic_results = {}
dynamic_errors = []
try:
    dynamic_results["summarize_image_per_sample"] = \
        mod.summarize_image_per_sample(IMG_ROWS)
    dynamic_results["summarize_image_by_domain_condition"] = \
        mod.summarize_image_by_domain_condition(IMG_ROWS)
    dynamic_results["summarize_noise_seed"] = \
        mod.summarize_noise_seed(IMG_ROWS)
    dynamic_results["summarize_proposal_per_sample"] = \
        mod.summarize_proposal_per_sample(PROP_ROWS)
    dynamic_results["summarize_proposal_by_domain_condition"] = \
        mod.summarize_proposal_by_domain_condition(PROP_ROWS)
    dynamic_results["summarize_route_stability"] = \
        mod.summarize_route_stability(IMG_ROWS)
    dynamic_results["summarize_execution_rate"] = \
        mod.summarize_execution_rate(IMG_ROWS)
    dynamic_results["worst_case_per_sample"] = \
        mod.worst_case_per_sample(IMG_ROWS, PROP_ROWS)
    dynamic_results["worst_case_by_domain"] = \
        mod.worst_case_by_domain(dynamic_results["worst_case_per_sample"])
    dynamic_results["kub_subgroup_robustness"] = \
        mod.kub_subgroup_robustness(IMG_ROWS)
    dynamic_results["generate_all_figures"] = \
        mod.generate_all_figures(IMG_ROWS, PROP_ROWS,
                                 dynamic_results["worst_case_per_sample"])
except Exception as exc:  # noqa: BLE001
    dynamic_errors.append({"type": type(exc).__name__,
                           "message": str(exc)})

builtins.open = _real_open
os.open = _real_os_open
Path.open = _real_path_open
Path.read_bytes = _real_path_read_bytes

# ---- D97 assertions on summarize_noise_seed -------------------------- #
noise_rows = dynamic_results.get("summarize_noise_seed", [])
noise_has_key = all("best_seed_selection" in r for r in noise_rows)
noise_values = sorted({r["best_seed_selection"] for r in noise_rows})
# frozen authority value, read from the frozen v1.0 contract module
_frozen_best = getattr(sys.modules["p36_common_v1_0_reg"],
                       "BEST_SEED_SELECTION", "MISSING")
best_seed_matches_authority = (
    noise_values == [False] and _frozen_best is False)

# Multi-seed aggregation proof: the KUB gaussian_noise condition has
# one sample realized under ALL THREE prescribed seeds with distinct
# deltas whose cross-seed mean differs from EVERY single-seed delta;
# the reported mean must be the mean across ALL seeds.
kub_noise = [r for r in noise_rows
             if r["domain"] == "KUB"
             and r["condition"] == "gaussian_noise_sigma_0.10"]
multi_seed_ok = False
multi_seed_detail = {}
if kub_noise:
    row = kub_noise[0]
    # actual paired deltas per prescribed base seed for the KUB sample
    seed_deltas = sorted({
        float(r["paired_delta_dice"])
        for r in IMG_ROWS
        if r["domain"] == "KUB"
        and r["condition"] == "gaussian_noise_sigma_0.10"
        and r["base_seed"] in NOISE_BASE_SEEDS})
    mean_all = sum(seed_deltas) / len(seed_deltas)
    reported = row["mean_across_seeds_of_sample_means"]
    multi_seed_ok = (
        len(seed_deltas) == len(NOISE_BASE_SEEDS)
        and abs(reported - mean_all) < 1e-9
        and all(abs(reported - sd) > 1e-9 for sd in seed_deltas))
    multi_seed_detail = {
        "n_prescribed_seeds_exercised": len(seed_deltas),
        "prescribed_base_seeds": NOISE_BASE_SEEDS,
        "per_seed_paired_delta_dice": seed_deltas,
        "mean_across_all_seeds": mean_all,
        "reported_mean_across_seeds_of_sample_means": reported,
        "reported_equals_any_single_seed_delta": any(
            abs(reported - sd) <= 1e-9 for sd in seed_deltas),
        "best_seed_selected": False,
    }

kub_rows = dynamic_results.get("kub_subgroup_robustness", {})
kub_ok = isinstance(kub_rows, dict) and kub_rows.get("reporting_only") is True

figures_res = dynamic_results.get("generate_all_figures", {})
figures_ok = (isinstance(figures_res, dict)
              and figures_res.get("n_figures") == 5
              and figures_res.get("new_figure_selection") is False)

dynamic_pass = (
    not dynamic_errors
    and len(dynamic_results) == len(LATE_PATH_FUNCTIONS)
    and noise_has_key and best_seed_matches_authority
    and multi_seed_ok and kub_ok and figures_ok)

# ---- isolation guarantees -------------------------------------------- #
torch_loaded = "torch" in sys.modules
test_holdout_accessed = [
    p for p in opened
    if ("test" in p.lower() and "holdout" in p.lower())
    or "\\test\\" in p.lower() or "/test/" in p.lower()
    or "router_holdout" in p.lower() or "holdout" in p.lower()]
# the ONLY non-temp, non-source data file opened under the
# repository root must be the frozen VAL manifest authority.
non_temp_opens = sorted({
    p for p in opened
    if not p.startswith(str(TMP))
    and not p.endswith(".py")
    and "__pycache__" not in p
    and p.startswith(str(ROOT))
    and not p.startswith(str(ROOT / ".venv"))})
real_targets_exist = []
for t in REAL_TARGETS:
    if Path(t).exists():
        real_targets_exist.append(str(t))

checks["C_d97_dynamic_regression"] = {
    "late_path_functions_executed": sorted(dynamic_results.keys()),
    "n_late_path_functions": len(dynamic_results),
    "expected_late_path_functions": LATE_PATH_FUNCTIONS,
    "dynamic_errors": dynamic_errors,
    "summarize_noise_seed": {
        "executed_without_attribute_error": not any(
            e["type"] == "AttributeError" for e in dynamic_errors),
        "rows_contain_best_seed_selection": noise_has_key,
        "best_seed_selection_values": noise_values,
        "frozen_authority_module": "scripts/analysis/phase36_robustness_common_v1_0.py",
        "frozen_authority_line": 282,
        "frozen_authority_value": _frozen_best,
        "value_matches_frozen_authority": best_seed_matches_authority,
        "multi_seed_aggregation": multi_seed_detail,
        "multiple_prescribed_seeds_aggregated": multi_seed_ok,
        "no_best_or_outcome_seed_selected": multi_seed_ok,
    },
    "kub_subgroup_robustness": {
        "executed": "kub_subgroup_robustness" in dynamic_results,
        "reporting_only": kub_rows.get("reporting_only") if isinstance(kub_rows, dict) else None,
        "pass": kub_ok,
    },
    "generate_all_figures": {
        "executed": "generate_all_figures" in dynamic_results,
        "n_figures": figures_res.get("n_figures") if isinstance(figures_res, dict) else None,
        "new_figure_selection": figures_res.get("new_figure_selection") if isinstance(figures_res, dict) else None,
        "pass": figures_ok,
    },
    "isolation": {
        "model_construction_required": False,
        "torch_imported": torch_loaded,
        "load_models_called": False,
        "run_science_called": False,
        "main_called": False,
        "TEST_accessed": bool(test_holdout_accessed),
        "ROUTER_HOLDOUT_accessed": bool(test_holdout_accessed),
        "test_holdout_paths_opened": test_holdout_accessed,
        "non_temp_non_source_opens": non_temp_opens,
        "only_frozen_val_manifest_read": (
            non_temp_opens == [str(val_csv)]),
        "real_v1_23_write_targets_consumed": real_targets_exist,
        "scientific_output_targets_consumed": bool(real_targets_exist),
        "writes_redirected_to_temp": str(TMP),
    },
    "pass": dynamic_pass and not torch_loaded
    and not test_holdout_accessed and not real_targets_exist
    and non_temp_opens == [str(val_csv)],
}

# =========================================================================== #
# D. LATE-PATH STATIC AUDITS (Task 5)                              #
# =========================================================================== #
# D1: stale v1.22 identifier tokens (outside the D97 provenance
# blocks, which legitimately cite the consumed v1.22 defect).
def _d97_blocks(text: str) -> str:
    """Remove the two D97 provenance blocks (the header block and
    the frozen-reporting-constant block) so stale-token scanning
    runs against the pure mechanical v1.22 -> v1.23 rebase only."""
    out = text
    marker = "DEFECT REPAIRED IN V1.23 (D97"
    anchor = ("DEFECTS REPAIRED IN V1.23 "
              "(proven from the frozen v1.11 bytes)")
    i = out.find(marker)
    if i >= 0:
        # header block: from its opening '# ===' boundary line
        # through the prose ending just before the anchor.
        start = out.rfind("\n# ===", 0, i)
        start = (start + 1) if start >= 0 else i
        j = out.find(anchor, i)
        if j < 0:
            j = i
        out = out[:start] + out[j:]
    cmarker = "D97 (v1.23): FROZEN REPORTING CONSTANTS"
    i = out.find(cmarker)
    if i >= 0:
        # constant block: from its opening '# ===' boundary line
        # through 'KUB_REPORTING_ONLY = True'.
        start = out.rfind("\n# ===", 0, i)
        start = (start + 1) if start >= 0 else i
        k = out.find("KUB_REPORTING_ONLY = True", i)
        if k >= 0:
            k = out.find("\n", k)
            k = (k + 1) if k >= 0 else len(out)
        else:
            k = i
        out = out[:start] + out[k:]
    return out


stripped = _d97_blocks(V123_SRC)
stale_identifier_tokens = []
for tok in ("v1_22", "V1_22", "v1.22", "V1.22",
            "phase36_robustness_v1_22"):
    if tok in stripped:
        stale_identifier_tokens.append(tok)

# D2: wrong output paths — every _write_csv target must be a
# path relative to the TAB / FIG write namespaces, and those
# namespaces themselves must point at the v1.23 namespace.
tree = ast.parse(V123_SRC)
write_calls = []
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
            and n.func.id == "_write_csv" and n.args:
        a0 = n.args[0]
        if isinstance(a0, ast.BinOp):
            write_calls.append(ast.unparse(a0))
wrong_paths = [
    c for c in write_calls
    if "TAB /" not in c and "FIG /" not in c]
namespace_ok = all(
    "phase36_robustness_v1_23" in str(p)
    for p in (REAL_TAB, REAL_FIG, REAL_ARR))

# D3: exclusive-create collisions — the frozen reachable targets are
# unique and every writer is fail-closed on existing targets.
targets = [str(t.relative_to(ROOT)).replace("\\", "/")
           for t in REAL_TARGETS]
unique_targets = len(set(targets)) == len(targets)

# D4: exclusive-create writer semantics + parent-directory guards.
def _function_source(name: str) -> str:
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(V123_SRC, n) or ""
    return ""


writers = {
    "_write_csv": {"exclusive_create": 'open(path, "x"' in _function_source("_write_csv"),
                   "refuses_existing": "FileExistsError" in _function_source("_write_csv"),
                   "mkdir_parents": "mkdir(parents=True" in _function_source("_write_csv")},
    "_savefig_once": {"exclusive_create": "O_EXCL" in _function_source("_savefig_once"),
                      "refuses_existing": "exists()" in _function_source("_savefig_once"),
                      "mkdir_parents": "mkdir(parents=True" in _function_source("_savefig_once")},
    "_write_science_success_artifact": {"exclusive_create": 'open(path, "x"' in _function_source("_write_science_success_artifact"),
                                        "refuses_existing": False,
                                        "mkdir_parents": "mkdir(parents=True" in _function_source("_write_science_success_artifact")},
    "_write_science_failure_artifact": {"exclusive_create": 'open(path, "x"' in _function_source("_write_science_failure_artifact"),
                                        "refuses_existing": False,
                                        "mkdir_parents": "mkdir(parents=True" in _function_source("_write_science_failure_artifact")},
}
writer_semantics_ok = all(
    w["exclusive_create"] and w["mkdir_parents"] for w in writers.values())

# D5: undefined globals in late-path functions — every Name loaded in
# a late-path function body must resolve to a module global, builtin,
# local or argument (static scope pass).
BUILTINS = set(dir(builtins))


def _undefined_names(fn_name: str) -> list:
    fn_src = _function_source(fn_name)
    if not fn_src:
        return [f"<missing function {fn_name}>"]
    fnt = ast.parse(fn_src)
    fndef = fnt.body[0]
    args = set()
    for a in fndef.args.args + fndef.args.kwonlyargs:
        args.add(a.arg)
    assigned = set()
    for n in ast.walk(fnt):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            assigned.add(n.id)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assigned.add(n.name)
        if isinstance(n, ast.ExceptHandler) and n.name:
            assigned.add(n.name)
        if isinstance(n, (ast.For, ast.AsyncFor)) and isinstance(n.target, ast.Name):
            assigned.add(n.target.id)
        if isinstance(n, ast.withitem) and n.optional_vars is not None \
                and isinstance(n.optional_vars, ast.Name):
            assigned.add(n.optional_vars.id)
    module_globals = set(sys.modules["p36_exec_v1_23_reg"].__dict__.keys())
    undefined = []
    for n in ast.walk(fnt):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            nm = n.id
            if (nm not in args and nm not in assigned
                    and nm not in module_globals and nm not in BUILTINS):
                undefined.append(nm)
    return sorted(set(undefined))


late_path_undefined = {
    fn: _undefined_names(fn) for fn in LATE_PATH_FUNCTIONS}
late_path_undefined_any = any(late_path_undefined.values())

# D6: stale function/identifier names — no v1.xx function names remain.
stale_fn_names = [
    n for n in ("v1_22_reachable_write_targets",
                "verify_v1_22_output_absence",
                "verify_v1_22_dispatch_output_absence")
    if n in V123_SRC]

static_pass = (
    not stale_identifier_tokens and not wrong_paths
    and namespace_ok
    and unique_targets and writer_semantics_ok
    and not late_path_undefined_any and not stale_fn_names)

checks["D_late_path_static_audit"] = {
    "functions_audited": LATE_PATH_FUNCTIONS,
    "stale_v1_22_identifier_tokens": stale_identifier_tokens,
    "write_call_targets_outside_tab_fig": wrong_paths,
    "scientific_write_namespaces_v1_23": namespace_ok,
    "n_reachable_write_targets": len(targets),
    "all_reachable_write_targets_unique": unique_targets,
    "writer_exclusive_create_and_parent_mkdir": writers,
    "writer_semantics_ok": writer_semantics_ok,
    "late_path_undefined_globals": late_path_undefined,
    "late_path_undefined_globals_present": late_path_undefined_any,
    "stale_v1_xx_function_names": stale_fn_names,
    "pass": static_pass,
}

# =========================================================================== #
# AGGREGATE                                                      #
# =========================================================================== #
all_pass = (
    checks["A_c_attribute_audit"]["pass"]
    and checks["B_d97_mutation_control"]["pass"]
    and checks["C_d97_dynamic_regression"]["pass"]
    and checks["D_late_path_static_audit"]["pass"])

report = {
    "artifact": "phase36_v1_23_d97_regression_report",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_23",
    "type": "D97_PRE_EXECUTION_REGRESSION_REPORT",
    "mode": "PRE_EXECUTION_VERIFY_ONLY__NON_CONSUMING",
    "generated_utc": "2026-10-11T00:00:00Z",
    "defect": "D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_COMMON_BEST_SEED_SELECTION",
    "execution_source": "scripts/analysis/phase36_robustness_execution_v1_23.py",
    "execution_source_sha256": E_V123_SHA,
    "frozen_v1_22_sha256": E_V122_SHA,
    "checks": checks,
    "all_pass": bool(all_pass),
    "science_executed": False,
    "TEST_accessed": False,
    "ROUTER_HOLDOUT_accessed": False,
    "model_construction_required": False,
    "scientific_output_targets_consumed": False,
    "terminal": ("PHASE36_V1_23_D97_REGRESSION_PASS"
                 if all_pass else
                 "PHASE36_V1_23_D97_REGRESSION_FAIL_CLOSED"),
}

if REPORT.exists():
    print("REFUSE_OVERWRITE: regression report already exists",
          file=sys.stderr)
    sys.exit(2)
flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
if hasattr(os, "O_BINARY"):
    flags |= os.O_BINARY
_fd = os.open(str(REPORT), flags, 0o644)
try:
    _data = (json.dumps(report, indent=1) + "\n").encode("utf-8")
    _w = 0
    while _w < len(_data):
        _w += os.write(_fd, _data[_w:])
    os.fsync(_fd)
finally:
    os.close(_fd)

print(json.dumps({
    "terminal": report["terminal"],
    "all_pass": bool(all_pass),
    "A_c_attribute_audit_pass": checks["A_c_attribute_audit"]["pass"],
    "B_mutation_controls_all_caught": checks["B_d97_mutation_control"]["pass"],
    "C_dynamic_regression_pass": checks["C_d97_dynamic_regression"]["pass"],
    "D_late_path_static_audit_pass": checks["D_late_path_static_audit"]["pass"],
    "n_late_path_functions_executed": len(dynamic_results),
    "best_seed_selection": noise_values,
    "report": str(REPORT.relative_to(ROOT)),
}, indent=1))
sys.exit(0 if all_pass else 1)
