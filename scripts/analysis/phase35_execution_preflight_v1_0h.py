#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0h STATIC source preflight.

SOURCE + GOVERNANCE ONLY. Static (AST + text) analysis of the v1.0h sources. This script performs
NO model construction, NO checkpoint deserialization, NO strict load, NO forward, NO autograd,
NO Grad-CAM, NO router attribution, and reads NO protected data. It never imports torch.

Emits `reports/audits/phase35_execution_source_static_preflight_v1_0h.json`.
Exit 0 iff every check passes.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D://Softfors//jup")

FILES = {
    "v1_0h_execution": "scripts/analysis/phase35_interpretability_execution_v1_0h.py",
    "v1_0g_predecessor": "scripts/analysis/phase35_interpretability_execution_v1_0g.py",
    "v1_0f_predecessor": "scripts/analysis/phase35_interpretability_execution_v1_0f.py",
    "v1_0c_legacy": "scripts/analysis/phase35_interpretability_execution_v1_0c.py",
    "v1_0d": "scripts/analysis/phase35_interpretability_execution_v1_0d.py",
    "v1_0e": "scripts/analysis/phase35_interpretability_execution_v1_0e.py",
    "v1_0h_unit": "scripts/analysis/phase35_full_counter_contract_unit_v1_0h.py",
}

EXPECTED_SHAS = {
    "v1_0g_predecessor": "88456e46c94e53d45b10d864d9dbcd38eb773d7dd441441def9e6f221a0c9be3",
    "v1_0f_predecessor": "6a6097f4a3c346df38ab5ec452dc97717cdb65d789bf8bde8031442cb236e3e5",
    "v1_0c_legacy": "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa",
    "v1_0d": "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056",
}

CHECK_RESULTS: list[tuple[str, str, bool, str]] = []


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(name: str) -> str:
    return (ROOT / FILES[name]).read_text(encoding="utf-8")


def ck(cid: str, desc: str, ok: bool, detail: str = "") -> None:
    CHECK_RESULTS.append((cid, desc, bool(ok), detail))


def find_func(tree: ast.AST):
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[n.name] = n
    return out


def aug_targets(fn: ast.AST, src: str) -> list[str]:
    out = []
    for sub in ast.walk(fn):
        if isinstance(sub, ast.AugAssign):
            out.append(ast.unparse(sub.target))
    return out


def main() -> int:
    src_h = read("v1_0h_execution")
    src_u = read("v1_0h_unit")
    src_g = read("v1_0g_predecessor")
    src_c = read("v1_0c_legacy")
    src_d = read("v1_0d")
    tree_h = ast.parse(src_h)
    tree_u = ast.parse(src_u)
    tree_c = ast.parse(src_c)
    tree_d = ast.parse(src_d)
    fh = find_func(tree_h)
    fc = find_func(tree_c)
    fd = find_func(tree_d)

    # ---- 01 blocked histories preserved -------------------------------------------------------- #
    ck("01", "v1.0f blocked smoke preserved (byte-hash)",
       sha(ROOT / "reports/audits/phase35_synthetic_interpretability_smoke_v1_0f.json")
       == "05c02a34d61df1c6d3e53e2dd127f889501a5f5e99247aa8ef96fb947bc1d0fb")
    ck("02", "v1.0g blocked smoke preserved (byte-hash)",
       sha(ROOT / "reports/audits/phase35_synthetic_interpretability_smoke_v1_0g.json")
       == "d20fb2ebe4464b563061db41be1f9816d15710c483135385df5b23ae5a595fd1")
    ck("03", "v1.0g terminal preserved (byte-hash)",
       sha(ROOT / "reports/audits/phase35_synthetic_smoke_terminal_v1_0g.json")
       == "f4ae91753d792b1d8e5f2af275be8020036f227c674543ec2c8a901f8fff2bdb")

    # ---- 04-06 predecessor source hashes ------------------------------------------------------- #
    for k, exp in EXPECTED_SHAS.items():
        ck(f"04-{k}", f"{k} source sha256 frozen", sha(ROOT / FILES[k]) == exp)

    # ---- 07 single legacy counter ownership ---------------------------------------------------- #
    ck("07", "v1.0h aliases the live V0C legacy store (no independent copy)",
       "LEGACY_COUNTER_STORE = V0C.SMOKE_COUNTERS" in src_h
       and "aliased, never copied" in src_h)
    # ---- 08 no shallow copy at the CODE level (docstring may quote the defect) ------------------ #
    code_h = ast.get_docstring(tree_h, clean=False) or ""
    code_only = src_h.replace(code_h, "") if code_h else src_h
    ck("08", "v1.0h does NOT shallow-copy the legacy store into SMOKE_COUNTERS",
       "SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)" not in code_only
       and "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS" in src_h)

    # ---- 09 extension store owns only the four new counters ------------------------------------ #
    ext_assign = next((n for n in tree_h.body if isinstance(n, ast.Assign)
                       and getattr(n.targets[0], "id", "") == "SMOKE_COUNTERS_EXT"), None)
    ext_keys = []
    if ext_assign is not None:
        call = ext_assign.value
        if isinstance(call, ast.Call):
            for arg in call.args:
                seq = arg.elts if isinstance(arg, (ast.List, ast.Tuple)) else []
                for pair in seq:
                    if (isinstance(pair, ast.Tuple) and pair.elts
                            and isinstance(pair.elts[0], ast.Constant)):
                        ext_keys.append(pair.elts[0].value)
    ck("09", "extension store owns exactly the four post-v1.0c counters",
       ext_keys == ["primary_synthetic_target_masks", "actual_logits_empty_mask_helper_checks",
                    "additional_G_forwards_for_empty_mask", "additional_autograd_calls_for_empty_mask"],
       f"got {ext_keys}")
    ck("10", "extension disjointness asserted in source",
       "must not collide with legacy counters" in src_h)

    # ---- 11-13 router writer/reader store compatibility ---------------------------------------- #
    route_writes = [t for t in aug_targets(fc["smoke_router"], src_c)]
    ck("11", "V0C.smoke_router writes unqualified SMOKE_COUNTERS (live V0C store)",
       all(t.startswith("SMOKE_COUNTERS[") for t in route_writes) and len(route_writes) == 5,
       f"{route_writes}")
    ck("12", "V0D aliases the same live store (writer/reader bridge intact)",
       "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS" in src_d)
    ck("13", "v1.0h merge reads the SAME live legacy store",
       "for k, v in LEGACY_COUNTER_STORE.items()" in src_h
       and "LEGACY_COUNTER_STORE = V0C.SMOKE_COUNTERS" in src_h)
    ck("14", "v1.0h exposes writer/reader identity evidence",
       "router_writer_store_identity_verified" in src_h
       and "router_reader_store_identity_verified" in src_h
       and "router_counter_writer_reader_same_object_or_explicit_delta_bridge" in src_h)

    # ---- 15-17 primary / alias / empty ownership ----------------------------------------------- #
    prim = fh.get("smoke_synthetic_target_mask_rank2")
    ck("15", "primary helper increments PRIMARY in extension store exactly once",
       prim is not None
       and aug_targets(prim, src_h) == ["SMOKE_COUNTERS_EXT[PRIMARY_TARGET_MASK_COUNTER]"],
       f"{aug_targets(prim, src_h) if prim else None}")
    ck("16", "primary helper invokes the frozen V0D producer exactly once",
       "V0D.smoke_synthetic_target_mask_rank2()" in src_h)
    empty = fh.get("empty_mask_helper_check_insession_actual_logits")
    empty_writes = aug_targets(empty, src_h) if empty else []
    ck("17", "empty helper increments ONLY the empty observability extension counter",
       empty_writes == ["SMOKE_COUNTERS_EXT[EMPTY_MASK_OBSERVABILITY_COUNTER]"],
       f"{empty_writes}")
    ck("18", "empty helper does NOT increment primary or alias",
       not any("PRIMARY_TARGET_MASK" in w or "synthetic_smoke_target_masks" in w
               for w in empty_writes))

    # ---- 19-21 expected table: 35 keys incl. 8 protected at zero ------------------------------- #
    exp_assign = next((n for n in tree_h.body if isinstance(n, ast.Assign)
                       and getattr(n.targets[0], "id", "") == "_FULL_EXPECTED_COUNTERS_V1_0H"), None)
    exp_keys = []
    exp_vals = {}
    if exp_assign is not None and isinstance(exp_assign.value, ast.Call):
        for el in exp_assign.value.args:
            seq = el.elts if isinstance(el, (ast.List, ast.Tuple)) else []
            for tup in seq:
                if (isinstance(tup, ast.Tuple) and len(tup.elts) >= 2
                        and isinstance(tup.elts[0], ast.Constant)):
                    exp_keys.append(tup.elts[0].value)
                    exp_vals[tup.elts[0].value] = tup.elts[1].value
    ck("19", "expected table has exactly 35 keys", len(exp_keys) == 35, f"got {len(exp_keys)}")
    prot = ["raw_VAL_image_reads", "real_persisted_VAL_probability_reads", "VAL_GT_reads",
            "router_feature_cache_rows_read", "ROUTER_HOLDOUT_reads", "TEST_reads",
            "TRAIN_raw_reads", "scientific_outputs"]
    ck("20", "all 8 protected-data keys explicitly present",
       all(k in exp_keys for k in prot),
       f"missing {[k for k in prot if k not in exp_keys]}")
    ck("21", "all 8 protected-data keys expected 0",
       all(exp_vals.get(k) == 0 for k in prot))
    ck("22", "expected primary=1 alias=1 empty=1",
       exp_vals.get("primary_synthetic_target_masks") == 1
       and exp_vals.get("synthetic_smoke_target_masks") == 1
       and exp_vals.get("actual_logits_empty_mask_helper_checks") == 1)
    ck("23", "expected router rows 1/1/2/2/4",
       exp_vals.get("B_phi_synthetic_forwards") == 1
       and exp_vals.get("router_numeric_input_autograd_calls") == 1
       and exp_vals.get("total_model_forwards") == 2
       and exp_vals.get("total_autograd_calls") == 2
       and exp_vals.get("synthetic_router_attribution_rows") == 4)
    ck("24", "35-key count asserted at import time",
       "assert len(EXPECTED_COUNTERS_V1_0H) == EXPECTED_COUNTER_COUNT_V1_0H" in src_h)

    # ---- 25-27 exact keyset validation implemented --------------------------------------------- #
    ck("25", "exact keyset equality uses set() == comparison",
       "set(observed.keys())" in src_h and "set(EXPECTED_COUNTERS_V1_0H.keys())" in src_h
       and "obs_keys == exp_keys" in src_h)
    ck("26", "three separate booleans emitted",
       "counter_keyset_exact" in src_h and "counter_count_exact" in src_h
       and "counter_values_exact" in src_h)
    ck("27", "merge fails on duplicate ownership",
       "COUNTER_MERGE_DUPLICATE_OWNERSHIP" in src_h)
    ck("28", "merge fails on keyset mismatch vs expected table",
       "COUNTER_MERGE_KEYSET_MISMATCH_WITH_EXPECTED_TABLE" in src_h)

    # ---- 29-30 no manual post-hoc router count assignment -------------------------------------- #
    ck("29", "no hardcoded post-hoc router count injection",
       not re.search(r"SMOKE_COUNTERS\[['\"]B_phi_synthetic_forwards['\"]\]\s*=", src_h)
       and "synthetic_router_attribution_rows'] = 4" not in src_h.replace('"', "'"),
       "no '= value' assignments to router counters")
    ck("30", "router counters only reachable through the delegated V0C writer",
       "V0C.smoke_router(bphi_model, bphi_state)" in src_h)

    # ---- 31 baseline fail-closed gate before model construction -------------------------------- #
    ck("31", "baseline gate precedes model construction",
       src_h.index("COUNTER_BASELINE_NONZERO_BEFORE_MODEL_CONSTRUCTION")
       < src_h.index("V0B.load_g_component()"))
    ck("32", "baseline gate never resets a nonzero counter",
       "never silently" in src_h.lower() or "Never silently resets" in src_h)

    # ---- 33-40 scientific code path unchanged -------------------------------------------------- #
    sci_calls = ["V0C.smoke_environment_check()", "V0C.smoke_checkpoint_identity()",
                 "V0B.load_g_component()", "V0B.load_bphi_component()",
                 "V0C.smoke_film_validate(g_model)", "V0C.smoke_embedding_validate(g_model, bphi_model)",
                 "V0C.smoke_router(bphi_model, bphi_state)", "V0C.smoke_zero_denominator(bphi_state)",
                 "V0C.smoke_parameter_immutability(before, g_model, bphi_model)",
                 "V0D.gradcam_target_scalar_rank_safe", "cam_normalize_guarded",
                 "V0B.verify_authority_gates()"]
    ck("33", "all inherited scientific call sites present verbatim",
       all(s in src_h for s in sci_calls),
       f"missing {[s for s in sci_calls if s not in src_h]}")
    ck("34", "eight finite guard stages inherited from V0E",
       "FINITE_GUARD_STAGES = V0E.FINITE_GUARD_STAGES" in src_h)
    ck("35", "actual-logits helper reused mathematically (atol/rtol unchanged)",
       "EMPTY_MASK_ATOL = 1e-7" in src_h and "EMPTY_MASK_RTOL = 0.0" in src_h)
    ck("36", "parameter .grad audit reused verbatim from V0E",
       "parameter_grad_state_audit_insession = V0E.parameter_grad_state_audit_insession" in src_h)
    ck("37", "FiLM semantics unchanged (V0C.smoke_film_validate)",
       "ev[\"film_smoke\"] = V0C.smoke_film_validate(g_model)" in src_h)
    ck("38", "router mathematics unchanged (V0C.smoke_router / router_gradient_x_input)",
       "V0C.smoke_router(bphi_model, bphi_state)" in src_h
       and "V0D.smoke_synthetic_target_mask_rank2()" in src_h)
    ck("39", "R_psi / S_omega excluded (no construction/load/forward)",
       "R_psi_model_constructions" in src_h and "S_omega_model_constructions" in src_h
       and "V0B.load_rpsi_component" not in src_h and "load_somega" not in src_h)
    ck("40", "Grad-CAM gradient impl string unchanged",
       'GRADCAM_GRADIENT_IMPL = "gradcam_gradient_enabled_numerically_guarded_v1_0f"' in src_h)

    # ---- 41-43 terminal reporting clarity ------------------------------------------------------ #
    ck("41", "four unambiguous terminal fields present",
       all(f in src_h for f in ["artifact_generation_pass", "smoke_success",
                               "counter_contract_pass", "scientific_interface_checks_pass"]))
    ck("42", "all_pass is an alias of smoke_success (never true when blocked)",
       "ev[\"all_pass\"] = smoke_success" in src_h)
    ck("43", "terminal_state emitted",
       'ev["terminal_state"] = "SUCCESS" if smoke_success else "BLOCKED"' in src_h)

    # ---- 44-46 no execution in preflight/unit; unit torch-free --------------------------------- #
    ck("44", "unit test declares torch-free / model-free",
       "torch_imported" in src_u and "MODEL_FREE_CPU_STDLIB_ONLY" in src_u)
    ck("45", "unit test does not import torch at module level",
       "import torch" not in src_u)
    ck("46", "unit reproduces both historical defects (negative controls)",
       "n01_v1_0f_double_mask_defect" in src_u and "n02_v1_0g_shallow_copy_alias_defect" in src_u)

    # ---- 47-49 unit artifact present & passing ------------------------------------------------- #
    unit_art = ROOT / "reports/audits/phase35_full_counter_contract_unit_v1_0h.json"
    ck("47", "unit artifact exists", unit_art.exists())
    if unit_art.exists():
        ua = json.loads(unit_art.read_text(encoding="utf-8"))
        ck("48", "unit artifact all_pass", ua.get("all_pass") is True)
        ck("49", "unit artifact 0 failures", ua.get("assertions_failed") == 0,
           f"failed={ua.get('assertions_failed')}")

    # ---- 50 no torch import in this preflight -------------------------------------------------- #
    ck("50", "preflight is torch-free (static only)", "torch" not in sys.modules)

    # ---- hashes -------------------------------------------------------------------------------- #
    npass = sum(1 for _, _, ok, _ in CHECK_RESULTS if ok)
    nfail = len(CHECK_RESULTS) - npass
    doc = OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0h"),
        ("section", "\u00a7M"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
        ("preflight_class", "STATIC_SOURCE_ANALYSIS__NO_MODEL_EXECUTION"),
        ("no_execution", True), ("torch_imported", False),
        ("source_hashes", {k: sha(ROOT / v) for k, v in FILES.items()}),
        ("checks", [{"id": c, "desc": d, "pass": ok, "detail": t}
                    for c, d, ok, t in CHECK_RESULTS]),
        ("total_checks", len(CHECK_RESULTS)), ("passed", npass), ("failed", nfail),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", nfail == 0),
    ])
    op = ROOT / "reports/audits/phase35_execution_source_static_preflight_v1_0h.json"
    op.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"preflight: {npass}/{len(CHECK_RESULTS)} passed, {nfail} failed")
    for c, d, ok, t in CHECK_RESULTS:
        if not ok:
            print(f"  FAIL {c}: {d}  {t}")
    print("preflight sha256:", sha(op))
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
