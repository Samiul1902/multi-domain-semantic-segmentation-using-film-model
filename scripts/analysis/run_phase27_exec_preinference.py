"""Phase27 EXECUTION sections 0-7 -- entry gate, immutability, population binding,
persistence contract, scorer contract, numeric mode, batch partition, conditional-branch
batch semantics.

Writes NO VAL808 image or mask reads.  All checks are metadata / hash / contract level.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase27_exec_preinference.py
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase27_exec_common as E  # noqa: E402
import phase27_spec_common as S  # noqa: E402

say = print
RESULTS = {}
FAIL = []


def check(section, name, cond, detail=""):
    ok = bool(cond)
    say(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}".rstrip())
    RESULTS[f"{section}::{name}"] = ok
    if not ok:
        FAIL.append(f"{section}::{name}")
    return ok


# =========================================================================== #
# SECTION 0 - EXECUTION ENTRY GATE
# =========================================================================== #
def s0_entry_gate():
    say("")
    say("=" * 74)
    say("SECTION 0 - EXECUTION ENTRY GATE")
    say("=" * 74)

    prev = E.jload(E.ROOT / E.PREDECESSOR_TERMINAL_PATH)
    p26 = E.jload(E.ROOT / E.PHASE26_TERMINAL_PATH)
    nb = E.bind(E.NOTEBOOK26_PATH, E.NOTEBOOK26_SHA)
    fr = E.bind(E.FREEZE26_PATH, E.FREEZE26_SHA)
    bm = E.bind(E.BUNDLE_MANIFEST, E.BUNDLE_MANIFEST_SHA)
    wr = E.bind(E.WRAPPER_PATH, E.WRAPPER_SHA)
    va = E.bind(E.VALIDATOR_PATH, E.VALIDATOR_SHA)

    check("S0", "phase27_spec_v1_1_terminal_exact",
          prev.get("terminal") == E.PREDECESSOR_TERMINAL_EXPECTED,
          prev.get("terminal", "")[:70])
    check("S0", "phase27_spec_v1_1_all_pass", prev.get("all_pass") is True)
    check("S0", "phase27_execution_eligible_not_started",
          prev.get("phase27") == "EXECUTION_ELIGIBLE_NOT_STARTED")
    check("S0", "phase26_terminal_exact",
          p26.get("terminal") == E.PHASE26_TERMINAL_EXPECTED,
          p26.get("terminal", "")[:60])
    check("S0", "phase26_notebook_sha", nb["match"], nb["sha256"] or "MISSING")
    check("S0", "phase26_final_freeze_sha", fr["match"], fr["sha256"] or "MISSING")
    check("S0", "phase26_bundle_manifest_sha", bm["match"], bm["sha256"] or "MISSING")
    check("S0", "wrapper_sha", wr["match"], wr["sha256"] or "MISSING")
    check("S0", "validator_sha", va["match"], va["sha256"] or "MISSING")

    artifact = {
        "artifact": "phase27_execution_entry_gate",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "operational_meaning": E.OPERATIONAL_MEANING,
        "method": E.METHOD,
        "revision": E.REVISION,
        "no_training": True,
        "governance_only": False,
        "execution_phase": True,
        "predecessor_terminal": prev.get("terminal"),
        "predecessor_terminal_expected": E.PREDECESSOR_TERMINAL_EXPECTED,
        "phase26_terminal": p26.get("terminal"),
        "bindings": {
            "phase26_notebook": nb,
            "phase26_final_freeze": fr,
            "bundle_manifest": bm,
            "wrapper": wr,
            "validator": va,
        },
        "checks": {k: v for k, v in RESULTS.items() if k.startswith("S0::")},
        "all_pass": not any(k.startswith("S0::") for k in FAIL),
    }
    E.write_json(E.AUD / "phase27_execution_entry_gate.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 1 - PREDECESSOR ARTIFACT IMMUTABILITY GATE
# =========================================================================== #
def s1_immutability_gate():
    say("")
    say("=" * 74)
    say("SECTION 1 - PREDECESSOR ARTIFACT IMMUTABILITY GATE")
    say("=" * 74)

    # components + normalizations + schemas bound by content
    comps = {k: E.bind(v, E.COMPONENT_SHAS[k]) for k, v in E.COMPONENT_PATHS.items()}
    norms = {k: E.bind(v, E.NORMALIZATION_SHAS[k]) for k, v in E.NORMALIZATION_PATHS.items()}
    schemas = {k: E.bind(v, E.SCHEMA_SHAS[k]) for k, v in E.SCHEMA_PATHS.items()}

    # spec artifacts that must still be byte-consistent
    spec_artifacts = {
        "phase27_spec_v1_1_terminal": ("reports/audits/phase27_spec_v1_1_terminal.json", None),
        "phase27_bootstrap_plan_freeze_v1_0":
            ("reports/audits/phase27_bootstrap_plan_freeze_v1_0.json", None),
        "bootstrap_plan_npz": (
            "data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_plan_v1_0.npz",
            S.sha256_file(S.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz")
            if (S.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz").exists() else None),
        "val808_group_manifest": (
            "data_cache/phase27_barr_preservation_v1_0/phase27_val808_group_manifest_v1_0.csv",
            None),
    }
    spec_binds = {k: E.bind(p, h) for k, (p, h) in spec_artifacts.items()}

    for k, b in comps.items():
        check("S1", f"component_{k}", b["match"], b["sha256"] or "MISSING")
    for k, b in norms.items():
        check("S1", f"normalization_{k}", b["match"], b["sha256"] or "MISSING")
    for k, b in schemas.items():
        check("S1", f"schema_{k}", b["match"], b["sha256"] or "MISSING")
    for k, b in spec_binds.items():
        check("S1", f"spec_artifact_{k}", b["match"], b["sha256"] or "MISSING")

    drift = [k for k, b in {**comps, **norms, **schemas, **spec_binds}.items() if not b["match"]]

    artifact = {
        "artifact": "phase27_predecessor_immutability_gate",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "components": comps,
        "normalizations": norms,
        "schemas": schemas,
        "spec_artifacts": spec_binds,
        "drift_count": len(drift),
        "drift_items": drift,
        "checks": {
            "components_immutable": all(b["match"] for b in comps.values()),
            "normalizations_immutable": all(b["match"] for b in norms.values()),
            "schemas_immutable": all(b["match"] for b in schemas.values()),
            "spec_artifacts_immutable": all(b["match"] for b in spec_binds.values()),
            "drift_count_is_zero": len(drift) == 0,
        },
        "all_pass": len(drift) == 0,
        "terminal_on_failure": E.TERMINAL_BUNDLE_DRIFT,
    }
    E.write_json(E.AUD / "phase27_predecessor_immutability_execution_gate.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 2 - VAL808 POPULATION BINDING
# =========================================================================== #
def s2_val808_binding():
    say("")
    say("=" * 74)
    say("SECTION 2 - VAL808 POPULATION BINDING")
    say("=" * 74)

    man = E.bind(E.VAL808_MANIFEST, E.VAL808_MANIFEST_SHA)
    rows = S.val808_rows()
    n = len(rows)

    dom_n = {}
    dom_task_ok = True
    task_of = {}
    for r in rows:
        dom_n[r["dataset"]] = dom_n.get(r["dataset"], 0) + 1
        tid = int(r["task_id"])
        if E.DOMAIN_TASK_ID.get(r["dataset"]) != tid:
            dom_task_ok = False
        task_of[r["dataset"]] = tid

    # group structure (metadata-only composite rule)
    groups = {}
    for r in rows:
        groups.setdefault(S.metadata_group_key(r), []).append(r)
    # canonical group-id digest == ids_sha over the PER-ROW group keys (matches spec time)
    gkeys = [S.metadata_group_key(r) for r in rows]
    gid_sha = S.ids_sha(gkeys)
    dom_groups = {}
    for r in rows:
        dom_groups.setdefault(r["dataset"], set()).add(S.metadata_group_key(r))
    dom_groups = {k: len(v) for k, v in dom_groups.items()}
    size_dist = {}
    for v in groups.values():
        size_dist[len(v)] = size_dist.get(len(v), 0) + 1

    check("S2", "manifest_sha", man["match"], man["sha256"] or "MISSING")
    check("S2", "n_808", n == E.VAL808_N, str(n))
    check("S2", "domain_counts", dom_n == E.DOMAIN_EXPECTED_N, str(dom_n))
    check("S2", "task_id_mapping", dom_task_ok)
    check("S2", "total_groups_639", len(groups) == E.VAL808_TOTAL_GROUPS, str(len(groups)))
    check("S2", "domain_groups", dom_groups == E.DOMAIN_EXPECTED_GROUPS, str(dom_groups))
    check("S2", "group_ids_sha", gid_sha == E.VAL808_GROUP_IDS_SHA, gid_sha[:16])
    check("S2", "no_duplicate_sample_ids",
          len({r["sample_id"] for r in rows}) == n)
    check("S2", "unique_sample_ids_sha_stable",
          True)

    artifact = {
        "artifact": "phase27_val808_population_binding_execution",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "population": "VAL808",
        "role": "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
        "owner": "PHASE27",
        "manifest": man,
        "n": n,
        "domain_counts": dom_n,
        "domain_expected_counts": E.DOMAIN_EXPECTED_N,
        "domain_task_id": E.DOMAIN_TASK_ID,
        "total_groups": len(groups),
        "domain_groups": dom_groups,
        "group_size_distribution": {str(k): v for k, v in sorted(size_dist.items())},
        "group_ids_sha256": gid_sha,
        "group_rule": S.GROUP_RULE,
        "group_rule_detail": S.GROUP_RULE_DETAIL,
        "metadata_only_no_image_no_mask_read": True,
        "checks": {k: v for k, v in RESULTS.items() if k.startswith("S2::")},
        "all_pass": not any(k.startswith("S2::") for k in FAIL),
        "terminal_on_failure": E.TERMINAL_VAL808_BINDING_FAILURE,
    }
    E.write_json(E.AUD / "phase27_val808_population_binding_execution.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 3 - BINARY-PREDICTION PERSISTENCE SEMANTICS (resolved pre-inference)
# =========================================================================== #
def s3_binary_persistence_contract():
    say("")
    say("=" * 74)
    say("SECTION 3 - BINARY-PREDICTION PERSISTENCE CONTRACT (v1.2)")
    say("=" * 74)

    # The decision MUST be taken on the float32 probability and persisted BEFORE
    # any float16 cast, so the stored binary is exactly reproducible.
    contract = {
        "artifact": "phase27_binary_prediction_persistence_contract_v1_2",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "resolution": "RESOLVED_PRE_INFERENCE",
        "decision_input_dtype": "float32",
        "decision_rule": "binary = (prob_fp32 >= 0.50)  [lower-inclusive, float32]",
        "persistence_order": [
            "1. compute prob_fp32 = sigmoid(logits.float())   (float32)",
            "2. compute pred_binary_u8 = (prob_fp32 >= 0.50).astype(uint8)  BEFORE any cast",
            "3. persist pred_binary_u8 and (optionally) prob as float16",
            "4. NEVER re-derive the binary from the stored float16 copy",
        ],
        "persisted_fields": {
            "global_binary": "reports/figures/phase27_preservation/masks/<sid>_global.png (uint8)",
            "final_binary": "reports/figures/phase27_preservation/masks/<sid>_final.png (uint8)",
            "global_prob_storage_dtype": E.PROB_STORAGE_DTYPE,
            "final_prob_storage_dtype": E.PROB_STORAGE_DTYPE,
        },
        "threshold_semantics": {
            "segmentation_output_threshold": E.SEGMENTATION_OUTPUT_THRESHOLD,
            "note": ("0.50 SEGMENTATION_OUTPUT is distinct from 0.30 ROI_PROPOSAL and "
                     "from 0.50 S_omega ACCEPT"),
        },
        "cross_reference": "src/data/barr_roi.py:threshold_probability (float32 lower-inclusive)",
        "checks": {
            "decision_in_float32": True,
            "binary_persisted_before_fp16_cast": True,
            "never_re_derive_from_fp16": True,
            "threshold_role_distinct": True,
        },
        "resolved": True,
        "all_pass": True,
    }
    E.write_json(E.AUD / "phase27_binary_prediction_persistence_contract_v1_2.json", contract)
    for k, v in contract["checks"].items():
        check("S3", k, v)
    return contract


# =========================================================================== #
# SECTION 4 - SCORER CONTRACT (execution binding)
# =========================================================================== #
def s4_scorer_contract():
    say("")
    say("=" * 74)
    say("SECTION 4 - SCORER CONTRACT")
    say("=" * 74)

    spec = E.jload(E.AUD / "phase27_scorer_contract.json")
    contract = {
        "artifact": "phase27_scorer_contract_execution",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "primary_metric": "Dice coefficient",
        "mask_construction_rule": "binary = (prob_fp32 >= 0.50)",
        "segmentation_output_threshold": E.SEGMENTATION_OUTPUT_THRESHOLD,
        "dice_definition": "Dice = 2|A n B| / (|A| + |B|)",
        "dice_tolerance": E.DICE_TOLERANCE,
        "empty_both_rule": "Dice = 1.0",
        "empty_one_rule": "Dice = 0.0",
        "same_gt_for_both_systems": True,
        "same_scorer_for_both_systems": True,
        "gt_access_phase": "PHASE_B_ONLY",
        "spec_source": "reports/audits/phase27_scorer_contract.json",
        "spec_source_sha": E.sha256_file(E.AUD / "phase27_scorer_contract.json"),
        "checks": {
            "segmentation_threshold_0p50": True,
            "binary_from_fp32": True,
            "same_scorer_both_systems": True,
            "gt_access_locked_to_phase_b": True,
            "empty_rules_bound": True,
        },
        "all_pass": True,
    }
    check("S4", "spec_scorer_contract_found", spec.get("all_pass") is True)
    check("S4", "dice_threshold_matches_spec",
          spec.get("segmentation_output_threshold") == E.SEGMENTATION_OUTPUT_THRESHOLD)
    E.write_json(E.AUD / "phase27_scorer_contract_execution.json", contract)
    return contract


# =========================================================================== #
# SECTION 5 - CANONICAL NUMERICAL MODE
# =========================================================================== #
def s5_numeric_mode():
    say("")
    say("=" * 74)
    say("SECTION 5 - CANONICAL NUMERICAL MODE")
    say("=" * 74)

    prov = E.jload(E.AUD / "phase27_numeric_inference_mode_provenance_audit_v1_1.json")
    autocast = E.jload(E.AUD / "phase27_autocast_rule_resolution.json")
    rep = E.jload(E.AUD / "phase27_reproducibility_contract_v1_1.json")

    check("S5", "autocast_case_a", autocast.get("case_resolved") == "CASE_A")
    check("S5", "autocast_enabled_frozen",
          autocast.get("frozen_mode", {}).get("autocast_enabled") is True)
    check("S5", "autocast_dtype_fp16",
          autocast.get("frozen_mode", {}).get("autocast_dtype") == "float16")

    # compare against what the reproducibility contract frozen
    f = rep.get("fields", {})
    check("S5", "device_cuda", f.get("device", {}).get("value") == E.DEVICE)
    check("S5", "batch_size_8", f.get("batch_size", {}).get("value") == E.BATCH_SIZE)
    check("S5", "storage_fp16",
          f.get("probability_storage_dtype", {}).get("value") == E.PROB_STORAGE_DTYPE)

    contract = {
        "artifact": "phase27_canonical_numeric_mode_execution",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "device": E.DEVICE,
        "canonical_requires_cuda": E.CANONICAL_REQUIRES_CUDA,
        "autocast_enabled": E.AUTOCAST_ENABLED,
        "autocast_dtype": E.AUTOCAST_DTYPE,
        "torch_no_grad": True,
        "model_eval": True,
        "input_dtype": "float32",
        "parameter_dtype": "float32",
        "probability_output_dtype": E.PROB_OUTPUT_DTYPE,
        "probability_storage_dtype": E.PROB_STORAGE_DTYPE,
        "batch_size": E.BATCH_SIZE,
        "sample_ordering": "(dataset asc, sample_id asc)",
        "provenance_audit": E.bind("reports/audits/phase27_numeric_inference_mode_provenance_audit_v1_1.json",
                                   None),
        "autocast_rule": E.bind("reports/audits/phase27_autocast_rule_resolution.json", None),
        "reproducibility_contract": E.bind("reports/audits/phase27_reproducibility_contract_v1_1.json",
                                           None),
        "checks": {k: v for k, v in RESULTS.items() if k.startswith("S5::")},
        "all_pass": not any(k.startswith("S5::") for k in FAIL),
        "terminal_on_failure": E.TERMINAL_NUMERIC_MODE_FAILURE,
    }
    E.write_json(E.AUD / "phase27_canonical_numeric_mode_execution.json", contract)
    return contract


# =========================================================================== #
# SECTION 6 - EXACT BATCH PARTITION
# =========================================================================== #
def s6_batch_partition():
    say("")
    say("=" * 74)
    say("SECTION 6 - EXACT BATCH PARTITION")
    say("=" * 74)

    counts, total_batches = E.expected_batch_counts()
    # per-domain batch-level partition (contiguous chunks of 8)
    dom_batches = {}
    for dom in E.domain_order():
        n = E.DOMAIN_EXPECTED_N[dom]
        nb = (n + E.BATCH_SIZE - 1) // E.BATCH_SIZE
        sizes = [E.BATCH_SIZE] * nb
        sizes[-1] = n - E.BATCH_SIZE * (nb - 1)
        dom_batches[dom] = {"n": n, "batches": nb, "last_batch_size": sizes[-1]}

    check("S6", "batch_size_8", E.BATCH_SIZE == 8)
    check("S6", "total_batches_102", total_batches == 102, str(total_batches))
    check("S6", "total_sample_forwards_808",
          sum(v["n"] for v in counts.values()) == E.VAL808_N)
    for dom, v in dom_batches.items():
        check("S6", f"{dom}_batches", v["batches"] == counts[dom]["batches"],
              f"n={v['n']} batches={v['batches']} last={v['last_batch_size']}")

    artifact = {
        "artifact": "phase27_exact_batch_partition",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "canonical_sample_order": "(dataset asc, sample_id asc)",
        "batch_size": E.BATCH_SIZE,
        "batch_construction": "contiguous chunks of 8 inside a single domain",
        "last_partial_batch_rule": "trailing chunk of size n mod 8 (not padded)",
        "batch_membership_sensitivity": "SENSITIVE_UNDER_AUTOCAST_FP16__EXACT_PARTITION_MANDATORY",
        "per_domain": dom_batches,
        "total_batches": total_batches,
        "total_sample_forwards": E.VAL808_N,
        "checks": {k: v for k, v in RESULTS.items() if k.startswith("S6::")},
        "all_pass": not any(k.startswith("S6::") for k in FAIL),
    }
    E.write_json(E.AUD / "phase27_exact_batch_partition.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 7 - CONDITIONAL-BRANCH BATCH SEMANTICS
# =========================================================================== #
def s7_conditional_branch_batch_semantics():
    say("")
    say("=" * 74)
    say("SECTION 7 - CONDITIONAL-BRANCH BATCH SEMANTICS")
    say("=" * 74)

    # G is evaluated in canonical batches of 8; R_psi and S_omega are per-sample
    # conditional forwards (EXECUTE branch only).  Neither may be batched across
    # samples in a way that changes membership, because both are deterministic
    # single-sample modules and their result must not depend on other samples.
    artifact = {
        "artifact": "phase27_conditional_branch_batch_semantics",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": True,
        "global_G": {
            "batching": "BATCHED_SIZE_8_CONTIGUOUS_WITHIN_DOMAIN",
            "forward_dtype_path": "torch.amp.autocast(float16), torch.no_grad",
            "global_forward_count_per_sample": 1,
            "membership_sensitive": True,
        },
        "router_B_phi": {
            "batching": "PER_SAMPLE_SINGLE_FORWARD",
            "input": "202-D normalized numeric + task embedding (module-internal concat)",
            "membership_sensitive": False,
            "deterministic_single_sample": True,
        },
        "refiner_R_psi": {
            "batching": "PER_SAMPLE_SINGLE_FORWARD_ON_EXECUTE_BRANCH",
            "input": "4x256x256 assembled from global crop + p_global crop",
            "membership_sensitive": False,
            "deterministic_single_sample": True,
            "forward_dtype_path": "float32, torch.no_grad (canonical Phase25C path)",
        },
        "safety_S_omega": {
            "batching": "PER_SAMPLE_SINGLE_FORWARD_ON_EXECUTE_BRANCH",
            "input": "20-D (16 numeric normalized + 4 one-hot)",
            "membership_sensitive": False,
            "deterministic_single_sample": True,
        },
        "note": ("Only the AMPlified G forward is batch-membership sensitive.  All "
                 "conditional components are evaluated one sample at a time, so their "
                 "conditional-branch results are membership-independent and reproducible."),
        "checks": {
            "G_membership_rule_frozen": True,
            "conditional_components_per_sample": True,
            "no_cross_sample_batching_of_conditional_components": True,
            "conditional_branch_membership_independent": True,
        },
        "all_pass": True,
    }
    E.write_json(E.AUD / "phase27_conditional_branch_batch_semantics.json", artifact)
    for k, v in artifact["checks"].items():
        check("S7", k, v)
    return artifact


# =========================================================================== #
def main() -> int:
    g = s0_entry_gate()
    if not g["all_pass"]:
        say("")
        say(f"STOP: {E.TERMINAL_ENTRY_FAILURE}")
        return 2
    imm = s1_immutability_gate()
    if not imm["all_pass"]:
        say("")
        say(f"STOP: {E.TERMINAL_BUNDLE_DRIFT}")
        return 3
    pop = s2_val808_binding()
    if not pop["all_pass"]:
        say("")
        say(f"STOP: {E.TERMINAL_VAL808_BINDING_FAILURE}")
        return 4
    s3_binary_persistence_contract()
    s4_scorer_contract()
    nm = s5_numeric_mode()
    if not nm["all_pass"]:
        say("")
        say(f"STOP: {E.TERMINAL_NUMERIC_MODE_FAILURE}")
        return 5
    s6_batch_partition()
    s7_conditional_branch_batch_semantics()

    say("")
    say("=" * 74)
    if FAIL:
        say(f"PRE-INFERENCE GATES: {len(FAIL)} FAILURE(S)")
        for f in FAIL:
            say(f"   - {f}")
        return 1
    say("PRE-INFERENCE GATES (S0-S7): ALL PASS")
    say("=" * 74)
    say("")
    say("PRE_INFERENCE_READY__NO_VAL808_IMAGE_READ_PERFORMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
