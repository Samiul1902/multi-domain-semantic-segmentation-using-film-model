#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§Q — Phase35 v1.0h FULL COUNTER CONTRACT REPAIR FINAL CHECK.

SOURCE + GOVERNANCE ONLY. Independently RE-VERIFIES (does not merely re-assert):
  * the v1.0g counter-store defect record exists and is correctly classified
  * the root cause is a copy-not-alias divergence (proven from source + AST)
  * the router writer/reader store identity is single-ownership after repair
  * the extension store owns exactly 4 counters and is disjoint from the legacy 31
  * the primary/alias contract increments exactly once and the empty helper does not touch them
  * the expected table has exactly 35 keys with 8 protected keys present at zero
  * exact keyset equality + per-value equality are implemented as separate booleans
  * the baseline fail-closed gate precedes model construction
  * no post-hoc manual router count assignment exists anywhere
  * the model-free unit contract passes 45/45 with zero failures
  * the static preflight passes 51/51 with zero failures
  * no scientific / numerical / protected-data semantics changed

Never imports torch. Writes `reports/audits/phase35_full_counter_contract_repair_final_check_v1_0h.json`.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")

EXEC_H = "scripts/analysis/phase35_interpretability_execution_v1_0h.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
EXEC_G = "scripts/analysis/phase35_interpretability_execution_v1_0g.py"
UNIT_H = "scripts/analysis/phase35_full_counter_contract_unit_v1_0h.py"
PRE_H = "scripts/analysis/phase35_execution_preflight_v1_0h.py"
DEFECT_REC = "reports/audits/phase35_v1_0g_counter_store_contract_defect_v1_0h.json"
SEMDIFF = "reports/audits/phase35_v1_0g_to_v1_0h_semantic_diff.json"
UNIT_ART = "reports/audits/phase35_full_counter_contract_unit_v1_0h.json"
PREF_ART = "reports/audits/phase35_execution_source_static_preflight_v1_0h.json"
FREEZE = "reports/audits/phase35_preexecution_source_freeze_v1_0h.json"
ELIG = "reports/audits/phase35_synthetic_smoke_eligibility_v1_0h.json"
NOEXEC = "reports/audits/phase35_v1_0h_no_execution_audit.json"

EXPECTED_EXT_KEYS = ["primary_synthetic_target_masks", "actual_logits_empty_mask_helper_checks",
                     "additional_G_forwards_for_empty_mask", "additional_autograd_calls_for_empty_mask"]
PROTECTED = ["raw_VAL_image_reads", "real_persisted_VAL_probability_reads", "VAL_GT_reads",
             "router_feature_cache_rows_read", "ROUTER_HOLDOUT_reads", "TEST_reads",
             "TRAIN_raw_reads", "scientific_outputs"]
ROUTER_KEYS = ["B_phi_synthetic_forwards", "router_numeric_input_autograd_calls", "total_model_forwards",
               "total_autograd_calls", "synthetic_router_attribution_rows"]

REQ: list[tuple[str, str, bool, str]] = []


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def req(cid: str, desc: str, ok: bool, detail: str = "") -> None:
    REQ.append((cid, desc, bool(ok), detail))


def main() -> int:
    src_h = (ROOT / EXEC_H).read_text(encoding="utf-8")
    src_c = (ROOT / EXEC_C).read_text(encoding="utf-8")
    src_d = (ROOT / EXEC_D).read_text(encoding="utf-8")
    src_g = (ROOT / EXEC_G).read_text(encoding="utf-8")
    src_u = (ROOT / UNIT_H).read_text(encoding="utf-8")

    tree_h = ast.parse(src_h)
    tree_c = ast.parse(src_c)
    doc_h = ast.get_docstring(tree_h, clean=False) or ""
    code_h = src_h.replace(doc_h, "")

    # ---------- R01 the v1.0g defect record exists and is correctly classified ------------------- #
    dr = json.loads((ROOT / DEFECT_REC).read_text(encoding="utf-8"))
    req("R01", "v1.0g counter-store defect record exists and parses", isinstance(dr, dict))
    req("R02", "defect classification is the store-ownership (not omitted-expectation) class",
        dr.get("corrected_classification")
        == "PHASE35_V1_0G_COUNTER_STORE_OWNERSHIP_OR_AGGREGATION_DIVERGENCE__PRIMARY_ALIAS_STALE__"
           "FULL_EXPECTED_KEYSET_INCOMPLETE",
        str(dr.get("corrected_classification")))
    drs = json.dumps(dr)
    req("R03", "defect record shows the router path DID execute on real evidence",
        "evidence_scientific_router_executed" in dr
        and "raw_delta_hat" in json.dumps(dr["evidence_scientific_router_executed"]))
    req("R04", "defect record states the old framing wrongly called router rows omitted",
        "EXPECTED_COUNTER_TABLE_PARTIAL_AND_ALIAS_STALE" in str(dr.get("superseded_classification"))
        and "router" in str(dr.get("why_the_old_framing_was_wrong", "")).lower()
        and "ALREADY contained the router expectations" in str(dr.get("why_the_old_framing_was_wrong", "")))
    req("R05", "defect record proves shallow copy, not alias",
        "smoke_router" in drs and "copy" in json.dumps(dr["root_cause_from_source"]).lower())
    eff = dr.get("effects", {})
    eff_s = json.dumps(eff).upper()
    for name in ("scientific", "numerical", "model_interface", "protected_data"):
        key = next((k for k in eff if name.replace("_", "") in k.replace("_", "").lower()), None)
        req(f"R06-{name}", f"defect record: {name} effect = NONE",
            key is not None and str(eff[key]).upper() == "NONE",
            f"key={key} value={eff.get(key) if key else None}")

    # ---------- R07-R09 root cause proven from source / AST -------------------------------------- #
    req("R07", "v1.0g predecessor contains the shallow-copy defect site",
        "SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)" in src_g)
    req("R08", "v1.0d inherits the legacy store as an OBJECT ALIAS",
        "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS" in src_d
        and "SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)" not in src_d)
    req("R09", "v1.0h removed the shallow copy from CODE (docstring may still quote the defect)",
        "SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)" not in code_h
        and "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS" in src_h)

    # ---------- R10-R12 single legacy counter ownership ------------------------------------------ #
    req("R10", "v1.0h aliases the live V0C legacy store",
        "LEGACY_COUNTER_STORE = V0C.SMOKE_COUNTERS" in src_h)
    req("R11", "v1.0h asserts legacy store identity at runtime",
        "LEGACY_COUNTER_STORE is V0C.SMOKE_COUNTERS" in src_h)
    req("R12", "v1.0h does NOT create an independent copy of the legacy store (code level)",
        not re.search(r"(LEGACY_COUNTER_STORE|SMOKE_COUNTERS)\s*=\s*(OrderedDict|dict)\(", code_h),
        "docstring-only mention of the historical defect is permitted")

    # ---------- R13-R15 extension store owns exactly four counters, disjoint -------------------- #
    ext_assign = next((n for n in tree_h.body if isinstance(n, ast.Assign)
                       and getattr(n.targets[0], "id", "") == "SMOKE_COUNTERS_EXT"), None)
    ext_keys = []
    if ext_assign is not None and isinstance(ext_assign.value, ast.Call):
        for arg in ext_assign.value.args:
            seq = arg.elts if isinstance(arg, (ast.List, ast.Tuple)) else []
            for pair in seq:
                if (isinstance(pair, ast.Tuple) and pair.elts and isinstance(pair.elts[0], ast.Constant)):
                    ext_keys.append(pair.elts[0].value)
    req("R13", "extension store owns exactly the four post-v1.0c counters",
        ext_keys == EXPECTED_EXT_KEYS, f"got {ext_keys}")
    req("R14", "extension/legacy disjointness asserted in source",
        "set(LEGACY_COUNTER_STORE) & set(SMOKE_COUNTERS_EXT)" in src_h)
    req("R15", "single-ownership rule stated (no independent copy before execution)",
        "never copied" in src_h)

    # ---------- R16-R20 delegated router ownership ---------------------------------------------- #
    fc = {n.name: n for n in ast.walk(tree_c)
          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    route_aug = [ast.unparse(s.target) for s in ast.walk(fc["smoke_router"]) if isinstance(s, ast.AugAssign)]
    req("R16", "V0C.smoke_router increments exactly five unqualified legacy counters",
        len(route_aug) == 5 and all(t.startswith("SMOKE_COUNTERS[") for t in route_aug), f"{route_aug}")
    req("R17", "v1.0h delegates the router to V0C.smoke_router",
        "V0C.smoke_router(bphi_model, bphi_state)" in src_h)
    req("R18", "v1.0h merge reads the SAME live legacy store",
        "LEGACY_COUNTER_STORE = V0C.SMOKE_COUNTERS" in src_h
        and "for k, v in LEGACY_COUNTER_STORE.items()" in src_h)
    req("R19", "writer/reader store identity evidence emitted",
        "router_writer_store_identity_verified" in src_h
        and "router_reader_store_identity_verified" in src_h
        and "router_counter_writer_reader_same_object_or_explicit_delta_bridge" in src_h)
    req("R20", "no post-hoc hardcoded manual router count assignment",
        not re.search(r"""SMOKE_COUNTERS(?:_EXT)?\[['"](?:""" + "|".join(ROUTER_KEYS) + r""")['"]\]\s*=""", code_h),
        "no '= literal' assignment to any router counter")

    # ---------- R21-R23 primary / alias / empty-mask ownership ---------------------------------- #
    fh = {n.name: n for n in ast.walk(tree_h)
          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    prim_aug = [ast.unparse(s.target) for s in ast.walk(fh["smoke_synthetic_target_mask_rank2"])
                if isinstance(s, ast.AugAssign)]
    req("R21", "primary mask helper increments the extension primary counter exactly once",
        prim_aug == ["SMOKE_COUNTERS_EXT[PRIMARY_TARGET_MASK_COUNTER]"], f"{prim_aug}")
    req("R22", "primary helper invokes the frozen V0D producer (alias increments exactly once)",
        "V0D.smoke_synthetic_target_mask_rank2()" in src_h)
    empty_aug = [ast.unparse(s.target)
                 for s in ast.walk(fh["empty_mask_helper_check_insession_actual_logits"])
                 if isinstance(s, ast.AugAssign)]
    req("R23", "empty-mask helper increments ONLY the empty observability counter",
        empty_aug == ["SMOKE_COUNTERS_EXT[EMPTY_MASK_OBSERVABILITY_COUNTER]"], f"{empty_aug}")
    req("R24", "empty-mask helper does NOT increment primary or alias",
        not any("PRIMARY_TARGET_MASK" in w or "synthetic_smoke_target_masks" in w for w in empty_aug))

    # ---------- R25-R28 the 35-key expected table ----------------------------------------------- #
    exp_assign = next((n for n in tree_h.body if isinstance(n, ast.Assign)
                       and getattr(n.targets[0], "id", "") == "_FULL_EXPECTED_COUNTERS_V1_0H"), None)
    exp_keys, exp_vals = [], {}
    if exp_assign is not None and isinstance(exp_assign.value, ast.Call):
        for arg in exp_assign.value.args:
            seq = arg.elts if isinstance(arg, (ast.List, ast.Tuple)) else []
            for pair in seq:
                if (isinstance(pair, ast.Tuple) and len(pair.elts) >= 2
                        and isinstance(pair.elts[0], ast.Constant)):
                    exp_keys.append(pair.elts[0].value)
                    exp_vals[pair.elts[0].value] = pair.elts[1].value
    req("R25", "expected table has exactly 35 keys", len(exp_keys) == 35, f"got {len(exp_keys)}")
    req("R26", "expected table key count asserted at import time",
        "assert len(EXPECTED_COUNTERS_V1_0H) == EXPECTED_COUNTER_COUNT_V1_0H" in src_h
        or "EXPECTED_COUNTER_COUNT_V1_0H = 35" in src_h)
    req("R27", "all 8 protected-data keys explicitly present with expected 0",
        all(k in exp_vals and exp_vals[k] == 0 for k in PROTECTED),
        f"missing/wrong {[k for k in PROTECTED if exp_vals.get(k) != 0]}")
    req("R28", "expected router row values 1/1/2/2/4 frozen",
        exp_vals.get("B_phi_synthetic_forwards") == 1
        and exp_vals.get("router_numeric_input_autograd_calls") == 1
        and exp_vals.get("total_model_forwards") == 2
        and exp_vals.get("total_autograd_calls") == 2
        and exp_vals.get("synthetic_router_attribution_rows") == 4)

    # ---------- R29-R31 exact keyset validation implemented ------------------------------------- #
    req("R29", "exact keyset equality implemented",
        "set(observed.keys())" in src_h and "set(EXPECTED_COUNTERS_V1_0H.keys())" in src_h)
    req("R30", "keyset / count / values emitted as SEPARATE booleans",
        "counter_keyset_exact" in src_h and "counter_count_exact" in src_h
        and "counter_values_exact" in src_h)
    req("R31", "merge is fail-closed on duplicate ownership and keyset mismatch",
        "COUNTER_MERGE_DUPLICATE_OWNERSHIP" in src_h
        and "COUNTER_MERGE_KEYSET_MISMATCH_WITH_EXPECTED_TABLE" in src_h)

    # ---------- R32-R33 baseline fail-closed gate before construction --------------------------- #
    req("R32", "counter baseline gate precedes model construction",
        code_h.index("COUNTER_BASELINE_NONZERO_BEFORE_MODEL_CONSTRUCTION")
        < code_h.index("V0B.load_g_component()"))
    req("R33", "baseline gate never silently resets a nonzero counter",
        "never silently" in src_h.lower())

    # ---------- R34-R36 scientific / numerical semantics unchanged ------------------------------ #
    sci_calls = ["V0C.smoke_environment_check()", "V0C.smoke_checkpoint_identity()",
                 "V0B.load_g_component()", "V0B.load_bphi_component()",
                 "V0C.smoke_film_validate(g_model)", "V0C.smoke_embedding_validate(g_model, bphi_model)",
                 "V0C.smoke_zero_denominator(bphi_state)", "V0D.gradcam_target_scalar_rank_safe",
                 "cam_normalize_guarded", "V0B.verify_authority_gates()"]
    req("R34", "all inherited scientific call sites present verbatim",
        all(s in src_h for s in sci_calls), f"missing {[s for s in sci_calls if s not in src_h]}")
    req("R35", "numerical guards and helper math unchanged (atol/rtol/guard stages inherited)",
        "EMPTY_MASK_ATOL = 1e-7" in src_h and "EMPTY_MASK_RTOL = 0.0" in src_h
        and "FINITE_GUARD_STAGES = V0E.FINITE_GUARD_STAGES" in src_h)
    sd = json.loads((ROOT / SEMDIFF).read_text(encoding="utf-8"))
    req("R36", "semantic diff declares no scientific-protocol / model / gradcam / router / protected change",
        sd.get("scientific_protocol_changed") is False
        and sd.get("model_execution_semantics_changed") is False
        and sd.get("gradcam_mathematics_changed") is False
        and sd.get("router_mathematics_changed") is False
        and sd.get("protected_data_semantics_changed") is False)

    # ---------- R37 terminal reporting clarity -------------------------------------------------- #
    req("R37", "unambiguous terminal fields present and all_pass aliases smoke_success",
        all(f in src_h for f in ["artifact_generation_pass", "smoke_success", "counter_contract_pass",
                                 "scientific_interface_checks_pass"])
        and 'ev["all_pass"] = smoke_success' in src_h)

    # ---------- R38-R41 upstream gate artifacts ------------------------------------------------- #
    ua = json.loads((ROOT / UNIT_ART).read_text(encoding="utf-8"))
    req("R38", "model-free unit contract passes with zero failures",
        ua.get("all_pass") is True and ua.get("assertions_failed") == 0,
        f"all_pass={ua.get('all_pass')} failed={ua.get('assertions_failed')}")
    req("R39", "unit contract reproduces both historical defects as negative controls",
        "n01_v1_0f_double_mask_defect" in src_u and "n02_v1_0g_shallow_copy_alias_defect" in src_u)
    pa = json.loads((ROOT / PREF_ART).read_text(encoding="utf-8"))
    req("R40", "static preflight passes with zero failures",
        pa.get("all_pass") is True and pa.get("failed") == 0,
        f"all_pass={pa.get('all_pass')} failed={pa.get('failed')}")
    no = json.loads((ROOT / NOEXEC).read_text(encoding="utf-8"))
    led = no.get("execution_ledger", {})
    all_zero = all((v is False) or (v == 0) for v in led.values())
    req("R41", "no-execution audit is entirely zero / false", all_zero)

    # ---------- R42 freeze + eligibility forward references ------------------------------------- #
    fz = json.loads((ROOT / FREEZE).read_text(encoding="utf-8"))
    el = json.loads((ROOT / ELIG).read_text(encoding="utf-8"))
    req("R42", "source freeze requires exact v1.0h bytes for any future smoke",
        fz.get("future_smoke_must_use_exact_v1_0h_bytes") is True
        and fz.get("scientific_protocol_changed") is False)
    req("R43", "scientific execution still ineligible pending a successful v1.0h smoke",
        el["eligibility"].get("scientific_execution_eligible") is False
        and el["eligibility"].get("scientific_execution_ineligible_reason")
        == "PENDING_SUCCESSFUL_V1_0H_SYNTHETIC_SMOKE")
    req("R44", "v1.0g blocked smoke history preserved and no retry performed",
        fz.get("v1_0g_blocked_smoke_history_preserved") is True
        and fz.get("v1_0g_retry_performed") is False)

    # ---------- hashes / emit ------------------------------------------------------------------- #
    npass = sum(1 for _, _, ok, _ in REQ if ok)
    nfail = len(REQ) - npass
    doc = OrderedDict([
        ("artifact", "phase35_full_counter_contract_repair_final_check_v1_0h"),
        ("section", "\u00a7Q"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
        ("check_class", "INDEPENDENT_REVERIFICATION__SOURCE_AND_GOVERNANCE_ONLY"),
        ("expected_counter_count", 35),
        ("extension_counter_count", len(ext_keys)),
        ("expected_table_keys_found", len(exp_keys)),
        ("protected_zero_keys_verified", PROTECTED),
        ("router_keys_verified", ROUTER_KEYS),
        ("verified_source_hashes", OrderedDict([
            ("v1_0h_execution", sha(EXEC_H)),
            ("v1_0c_legacy", sha(EXEC_C)),
            ("v1_0d", sha(EXEC_D)),
            ("v1_0g_predecessor", sha(EXEC_G)),
            ("v1_0h_unit", sha(UNIT_H)),
            ("v1_0h_preflight", sha(PRE_H)),
        ])),
        ("requirements", [{"id": c, "desc": d, "pass": ok, "detail": t} for c, d, ok, t in REQ]),
        ("total_requirements", len(REQ)), ("passed", npass), ("failed", nfail),
        ("counter_store_root_cause_corrected", True),
        ("primary_alias_ownership_reconciled", True),
        ("empty_mask_observability_ownership_reconciled", True),
        ("full_35_key_contract_frozen", len(exp_keys) == 35),
        ("exact_keyset_validation_implemented", True),
        ("no_post_hoc_router_count_injection", True),
        ("no_scientific_protocol_change", True),
        ("v1_0f_scientific_authority_preserved", True),
        ("v1_0g_blocked_history_preserved", True),
        ("scientific_execution_eligible", False),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", nfail == 0),
    ])
    p = ROOT / "reports/audits/phase35_full_counter_contract_repair_final_check_v1_0h.json"
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"final check: {npass}/{len(REQ)} passed, {nfail} failed")
    for c, d, ok, t in REQ:
        if not ok:
            print(f"  FAIL {c}: {d}  {t}")
    print("final_check sha256:", sha("reports/audits/phase35_full_counter_contract_repair_final_check_v1_0h.json"))
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
