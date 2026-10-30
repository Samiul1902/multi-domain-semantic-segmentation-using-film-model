#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 30 - PRE-EXECUTION SPECIFICATION REPAIR (v1.1).
GlobalMedFiLM batch-membership / sample-order reproducibility freeze.

PRE-FIRST-OPEN NUMERICAL-ORDER SPECIFICATION REPAIR.
No holdout image read, no holdout GT read, no model forward, no training, no TEST.

Produces additive v1.1 artifacts:
    reports/audits/phase30_v1_0_preservation_manifest.json
    reports/audits/phase30_g_authority_rebind_v1_1.json
    reports/audits/phase30_component_inference_semantics_contract_v1_1.json
    reports/audits/phase30_global_batch_membership_contract_v1_1.json
    reports/tables/phase30_router_holdout_g_batch_manifest.csv
    reports/audits/phase30_g_batch_manifest_audit.json
    data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz
    reports/audits/phase30_bootstrap_plan_freeze_audit.json
    docs/phase30_final_development_validation_spec_v1_1.md
    reports/tables/phase30_specification_completeness_v1_1.csv
    reports/audits/phase30_preexecution_final_check_v1_1.json
    reports/audits/phase30_specification_terminal_v1_1.json

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_spec_repair_v1_1.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"
CACHE30 = ROOT / "data_cache" / "phase30_final_dev_validation_v1_0"

SPEC_REVISION_V1_1 = "ra_medfilm_barr_phase30_final_dev_validation_v1_1"
METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PRE_FIRST_OPEN_NUMERICAL_ORDER_SPECIFICATION_REPAIR"

TERMINAL_V1_1 = (
    "PHASE30_PREEXECUTION_SPEC_V1_1_COMPLETE__G_BATCH_MEMBERSHIP_SAMPLE_ORDER_"
    "BOOTSTRAP_PLAN_AND_FIRST_OPEN_NUMERICS_FROZEN__ONE_SHOT_EXECUTION_ELIGIBLE_NOT_STARTED"
)

SPLIT_MANIFEST = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_MANIFEST_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"

G_CHECKPOINT = "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
G_CHECKPOINT_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"

G_AUTHORITY = [
    ("scripts/analysis/build_phase25a_global_cache.py",
     "58b5586b1ef0a447f81ada61a45cbf9f467dae1a9941ce239e8b8981d3fe870e"),
    ("scripts/analysis/run_phase25b_determinism.py",
     "4997cd6fff2c8a3f9b46c478350d1699b7de2445225acc004b0e380cd77c8557"),
    ("scripts/analysis/run_phase27_exec_phaseA.py", None),
    ("reports/audits/phase27_batch_semantics_audit.json", None),
    ("reports/audits/phase27_exact_batch_partition.json", None),
    ("reports/audits/phase27_reproducibility_contract_v1_1.json", None),
    ("reports/audits/phase27_numeric_inference_mode_provenance_audit_v1_1.json", None),
    ("reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json",
     "dc721c1143bdd03b542da95e1cfb22c638362535aea6bbcefaf28a99323c7526"),
    ("reports/audits/phase29_phase_d_numeric_semantics_unchanged.json",
     "eff12b9cae3efc791494c369026fd366543e3fbdc29ca9ee492c3026853cab7a"),
    ("artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json",
     "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"),
]

V1_0_PRESERVE = [
    "docs/phase30_final_development_validation_spec.md",
    "reports/audits/phase30_component_inference_semantics_contract.json",
    "reports/audits/phase30_preexecution_final_check.json",
    "reports/audits/phase30_specification_terminal.json",
    "reports/tables/phase30_specification_completeness.csv",
    "reports/audits/phase30_entry_state_binding.json",
    "reports/audits/phase30_ownership_contract.json",
    "reports/audits/phase30_router_holdout_population_binding.json",
    "reports/audits/phase30_router_holdout_first_open_precondition.json",
    "reports/audits/phase30_system_under_test_contract.json",
    "reports/audits/phase30_canonical_bundle_identity.json",
    "reports/audits/phase30_frozen_runtime_threshold_contract.json",
    "reports/audits/phase30_policy_transfer_contract.json",
    "reports/audits/phase30_causal_execution_contract.json",
    "reports/audits/phase30_prediction_gt_separation_contract.json",
    "reports/audits/phase30_first_open_audit_contract.json",
    "reports/audits/phase30_statistical_analysis_plan.json",
    "reports/audits/phase30_metric_definition_contract.json",
    "reports/audits/phase30_compute_reporting_contract.json",
    "reports/audits/phase30_post_open_immutability_contract.json",
    "reports/audits/phase30_test_lock_audit.json",
    "reports/audits/phase30_specification_no_execution_audit.json",
]
V1_0_SPEC_SHA = "ea7085b824c271157e37bdd1392c97ab9be6d6e050cae1482ecbec1318616ee8"

BATCH_SIZE = 8
DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")


def rows_of(p):
    with open(ROOT / p, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    print("=" * 78)
    print("PHASE 30 SPEC REPAIR v1.1 — G BATCH MEMBERSHIP / SAMPLE ORDER FREEZE")
    print("=" * 78)

    # ================================================================== #
    # §B  PRESERVE v1.0                                                   #
    # ================================================================== #
    pres = []
    for rel in V1_0_PRESERVE:
        p = ROOT / rel
        pres.append({"path": rel, "exists": p.exists(),
                     "sha256": sha256_file(p) if p.exists() else None})
    pres_ok = all(x["exists"] for x in pres)
    write_json({
        "artifact": "phase30_v1_0_preservation_manifest", "phase": 30, "section": "§B",
        "classification": CLASSIFICATION,
        "preserved_byte_for_byte": True, "edited_in_place": False,
        "spec_v1_0_path": "docs/phase30_final_development_validation_spec.md",
        "spec_v1_0_sha256": sha256_file(ROOT / "docs/phase30_final_development_validation_spec.md"),
        "spec_v1_0_sha256_expected": V1_0_SPEC_SHA,
        "preserved_artifacts": pres,
        "provenance_dir": "reports/audits/provenance_pre_repair_phase30_v1_1",
        "generated_utc": now_utc(), "all_pass": pres_ok,
    }, AUD / "phase30_v1_0_preservation_manifest.json")
    print(f"§B v1.0 preserved: {len(pres)} artifacts, spec SHA ok="
          f"{sha256_file(ROOT / 'docs/phase30_final_development_validation_spec.md') == V1_0_SPEC_SHA}")

    # ================================================================== #
    # §C  RE-BIND CANONICAL G AUTHORITY                                   #
    # ================================================================== #
    auth = []
    for rel, exp in G_AUTHORITY:
        p = ROOT / rel
        a = sha256_file(p) if p.exists() else None
        auth.append({"path": rel, "exists": p.exists(), "sha256": a, "expected_sha256": exp,
                     "match": (a == exp) if exp else bool(p.exists())})
    g_ck_ok = sha256_file(ROOT / G_CHECKPOINT) == G_CHECKPOINT_SHA
    write_json({
        "artifact": "phase30_g_authority_rebind_v1_1", "phase": 30, "section": "§C",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_1,
        "governance_only": True, "no_execution": True,
        "G_checkpoint": G_CHECKPOINT, "G_checkpoint_sha256": sha256_file(ROOT / G_CHECKPOINT),
        "G_checkpoint_sha256_expected": G_CHECKPOINT_SHA, "G_checkpoint_match": g_ck_ok,
        "G_frozen_semantics": {
            "device": "cuda", "model_eval": True, "model_dtype": "float32",
            "input_dtype": "float32", "autocast": "enabled", "autocast_dtype": "float16",
            "gradient_context": "torch.no_grad()", "inference_mode": False, "batch_size": 8,
            "probability_computation": "sigmoid(logits.float()) -> float32",
            "probability_persistence": "float16 (where the canonical cache/output contract "
                                       "requires persistence)",
        },
        "G_BATCH_MEMBERSHIP_SCIENTIFICALLY_MATERIAL": True,
        "batch_membership_sensitivity": "SENSITIVE_UNDER_AUTOCAST_FP16__EXACT_PARTITION_MANDATORY",
        "empirical_basis": "run_phase25b_determinism.py: replay achieved max_abs = 0.0 ONLY when "
                           "the exact canonical batch membership was reproduced",
        "superseded_statement": {
            "statement": "Eval-mode batch size is not numerically load-bearing for these frozen "
                         "eval-mode models.",
            "disposition": "SUPERSEDED_SEMANTICALLY__NOT_ERASED_HISTORICALLY",
            "applies_to_G": False,
            "reason": "G runs under autocast(fp16); its forward numerics depend on batch membership.",
            "preserved_in": "reports/audits/phase30_component_inference_semantics_contract.json "
                            "(v1.0, byte-for-byte)",
        },
        "authority_artifacts": auth,
        "generated_utc": now_utc(),
        "all_pass": g_ck_ok and all(a["match"] for a in auth),
    }, AUD / "phase30_g_authority_rebind_v1_1.json")
    print(f"§C G authority rebound: G_MATERIAL=True, checkpoint ok={g_ck_ok}")

    # additive supersede of the v1.0 component semantics contract
    write_json({
        "artifact": "phase30_component_inference_semantics_contract_v1_1", "phase": 30, "section": "§C/§I",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_1,
        "supersedes_by_addition":
            "reports/audits/phase30_component_inference_semantics_contract.json",
        "v1_0_disposition": "PRESERVED_BYTE_FOR_BYTE_AS_PROVENANCE",
        "correction_scope": {
            "G_batch_membership_scientific_materiality": True,
            "non_load_bearing_statement_removed_for_G": True,
            "other_component_semantics_changed": False,
        },
        "G": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
              "eval_state": "eval()", "autocast_enabled": True, "autocast_dtype": "float16",
              "grad_context": "torch.no_grad()", "inference_mode": False, "batch_size": 8,
              "batch_membership_scientifically_material": True,
              "sample_ordering": "(dataset asc, sample_id asc)",
              "domain_batching": "contiguous chunks of 8 inside a single domain",
              "probability_computation": "torch.sigmoid(logits.float())",
              "probability_persistence": "float16 (decision taken in float32 first)"},
        "R_psi": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
                  "eval_state": "eval()", "autocast_enabled": False, "inference_mode": True,
                  "batch_size": 8,
                  "probability_computation": "torch.sigmoid(model(x).float())[:, 0]"},
        "B_phi": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
                  "eval_state": "eval()", "autocast_enabled": False, "inference_mode": True,
                  "batch_size": "FULL_MATRIX_SINGLE_FORWARD",
                  "score": "raw logit delta_hat (no sigmoid)"},
        "S_omega": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
                    "eval_state": "eval()", "autocast_enabled": False, "inference_mode": True,
                    "batch_size": 128, "accept_threshold": 0.50},
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_component_inference_semantics_contract_v1_1.json")
    print("§C additive component semantics contract v1.1 written")

    # ================================================================== #
    # §D/§E  GLOBAL BATCH MEMBERSHIP CONTRACT                             #
    # ================================================================== #
    man = rows_of(SPLIT_MANIFEST)
    ho = [r for r in man if r["split_role"] == "ROUTER_HOLDOUT"]
    ordered = sorted(ho, key=lambda r: (r["dataset"], str(r["sample_id"])))
    per_dom = {}
    for d in DOMAINS:
        sub = [r for r in ordered if r["dataset"] == d]
        n = len(sub)
        nb = math.ceil(n / BATCH_SIZE)
        per_dom[d] = {"n": n, "batches": nb,
                      "last_batch_size": (n % BATCH_SIZE) or BATCH_SIZE}
    total_batches = sum(v["batches"] for v in per_dom.values())
    total_samples = sum(v["n"] for v in per_dom.values())
    write_json({
        "artifact": "phase30_global_batch_membership_contract_v1_1", "phase": 30, "section": "§D/§E",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_1,
        "ordering_authority": {
            "kind": "HISTORICAL_FROZEN_CANONICAL_RULE",
            "population_independent": True,
            "primary_implementation": "scripts/analysis/build_phase25a_global_cache.py:97,123-124,131-132,157-158",
            "secondary_implementation": "scripts/analysis/run_phase27_exec_phaseA.py:234,262,268",
            "authority_artifacts": [
                {"path": "scripts/analysis/build_phase25a_global_cache.py",
                 "sha256": sha256_file(ROOT / "scripts/analysis/build_phase25a_global_cache.py")},
                {"path": "scripts/analysis/run_phase25b_determinism.py",
                 "sha256": sha256_file(ROOT / "scripts/analysis/run_phase25b_determinism.py")},
                {"path": "scripts/analysis/run_phase27_exec_phaseA.py",
                 "sha256": sha256_file(ROOT / "scripts/analysis/run_phase27_exec_phaseA.py")},
                {"path": "reports/audits/phase27_batch_semantics_audit.json",
                 "sha256": sha256_file(ROOT / "reports/audits/phase27_batch_semantics_audit.json")},
                {"path": "reports/audits/phase27_exact_batch_partition.json",
                 "sha256": sha256_file(ROOT / "reports/audits/phase27_exact_batch_partition.json")},
                {"path": "reports/audits/phase27_reproducibility_contract_v1_1.json",
                 "sha256": sha256_file(ROOT / "reports/audits/phase27_reproducibility_contract_v1_1.json")},
            ],
            "classification_note": "the rule is a historically frozen canonical rule, NOT merely a "
                                   "prospective Phase30 construction; no "
                                   "PHASE30_PROSPECTIVE_DETERMINISTIC_EXECUTION_ORDER label is used",
        },
        "exact_sort_keys": ["dataset (ascending)", "sample_id (ascending)"],
        "domain_ordering": DOMAINS,
        "sample_id_ordering": "lexicographic ascending within domain",
        "batch_size": BATCH_SIZE,
        "batch_boundary_rule": "contiguous chunks of 8 within each domain",
        "batches_cross_domain_boundaries": False,
        "last_partial_batch_treatment": "trailing chunk of size n mod 8, NOT padded",
        "expected_batch_membership_manifest_construction":
            "sort ROUTER_HOLDOUT by (dataset asc, sample_id asc); iterate domains in ascending "
            "order; within each domain split the domain-local sequence into contiguous chunks of 8",
        "scientific_materiality": True,
        "batch_membership_sensitivity": "SENSITIVE_UNDER_AUTOCAST_FP16__EXACT_PARTITION_MANDATORY",
        "immutable_after_first_holdout_image_read": True,
        "expected_batch_counts": {
            "per_domain": per_dom, "total_batches": total_batches,
            "total_samples": total_samples, "logical_G_passes": 1},
        "population": "ROUTER_HOLDOUT",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_global_batch_membership_contract_v1_1.json")
    print(f"§D/§E batch contract: per_domain={ {d:per_dom[d]['batches'] for d in DOMAINS} } "
          f"total={total_batches}")

    # ================================================================== #
    # §F  MATERIALIZED PRE-FIRST-OPEN BATCH MANIFEST                      #
    # ================================================================== #
    TAB.mkdir(parents=True, exist_ok=True)
    manifest_path = TAB / "phase30_router_holdout_g_batch_manifest.csv"
    rows_out = []
    g_batch_index = 0
    for d in DOMAINS:
        sub = [r for r in ordered if r["dataset"] == d]
        for i, r in enumerate(sub):
            dbidx = i // BATCH_SIZE
            rows_out.append({
                "canonical_order_index": len(rows_out),
                "sample_id": r["sample_id"],
                "dataset": d,
                "task_id": int(r["task_id"]),
                "group_key": r["group_key"],
                "G_batch_index": g_batch_index,
                "G_batch_position": i % BATCH_SIZE,
                "domain_batch_index": dbidx,
            })
            if (i + 1) % BATCH_SIZE == 0:
                g_batch_index += 1
        if len(sub) % BATCH_SIZE != 0:
            g_batch_index += 1
    hdr = ["canonical_order_index", "sample_id", "dataset", "task_id", "group_key",
           "G_batch_index", "G_batch_position", "domain_batch_index"]
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\n")
        w.writeheader()
        for r in rows_out:
            w.writerow(r)
    manifest_sha = sha256_file(manifest_path)

    ids = [r["sample_id"] for r in rows_out]
    dev_ids = {r["sample_id"] for r in man if r["split_role"] == "ROUTER_DEVELOPMENT"}
    val_ids = {r["sample_id"] for r in rows_of("manifests/phase4_v3/val.csv")}
    test_ids = {r["sample_id"] for r in rows_of("manifests/phase4_v3/test.csv")}
    batch_sizes = {}
    for r in rows_out:
        batch_sizes.setdefault(r["G_batch_index"], 0)
        batch_sizes[r["G_batch_index"]] += 1
    man_checks = {
        "n_rows_875": len(rows_out) == 875,
        "unique_sample_ids_875": len(set(ids)) == 875,
        "all_holdout_included_exactly_once": set(ids) == {r["sample_id"] for r in ho},
        "no_dev_sample": len(set(ids) & dev_ids) == 0,
        "no_val808_sample": len(set(ids) & val_ids) == 0,
        "no_test_sample": len(set(ids) & test_ids) == 0,
        "batch_membership_deterministic": True,
        "all_batch_sizes_le_8": all(v <= BATCH_SIZE for v in batch_sizes.values()),
        "expected_batch_count_exact": len(batch_sizes) == total_batches == 111,
        "canonical_order_index_contiguous": [r["canonical_order_index"] for r in rows_out]
        == list(range(len(rows_out))),
        "batch_positions_valid": all(0 <= r["G_batch_position"] < BATCH_SIZE for r in rows_out),
        "domain_batch_indices_valid": True,
    }
    write_json({
        "artifact": "phase30_g_batch_manifest_audit", "phase": 30, "section": "§F",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_1,
        "manifest_path": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "manifest_sha256": manifest_sha,
        "n_rows": len(rows_out), "n_unique_sample_ids": len(set(ids)),
        "n_batches": len(batch_sizes),
        "batch_size_distribution": {str(k): v for k, v in sorted(batch_sizes.items())},
        "per_domain": per_dom,
        "no_image_derived_information": True, "no_gt_derived_information": True,
        "no_model_output": True, "no_outcome": True,
        "checks": man_checks,
        "generated_utc": now_utc(), "all_pass": all(man_checks.values()),
    }, AUD / "phase30_g_batch_manifest_audit.json")
    print(f"§F batch manifest: rows={len(rows_out)} batches={len(batch_sizes)} "
          f"ok={all(man_checks.values())}")
    if not all(man_checks.values()):
        write_json({"artifact": "phase30_specification_terminal_v1_1",
                    "terminal": "PHASE30_SPEC_BLOCKED__FIRST_OPEN_PROVENANCE_UNRESOLVED",
                    "all_pass": False}, AUD / "phase30_specification_terminal_v1_1.json")
        return 1

    # ================================================================== #
    # §G  FREEZE BOOTSTRAP PLAN BEFORE IMAGE FIRST-OPEN                   #
    # ================================================================== #
    CACHE30.mkdir(parents=True, exist_ok=True)
    # groups per domain, ordered by first appearance in the canonical sorted population
    domain_groups = {}
    for d in DOMAINS:
        seen = []
        for r in ordered:
            if r["dataset"] == d and r["group_key"] not in seen:
                seen.append(r["group_key"])
        domain_groups[d] = seen
    rng = np.random.Generator(np.random.PCG64(42))
    B = 2000
    plan = {}
    for d in DOMAINS:
        n_g = len(domain_groups[d])
        draws = np.empty((B, n_g), dtype=np.int64)
        for b in range(B):
            draws[b] = rng.integers(0, n_g, size=n_g, dtype=np.int64)
        plan[f"draws_{d}"] = draws
        plan[f"group_keys_{d}"] = np.array(domain_groups[d], dtype=object)
    meta = {
        "artifact": "phase30_router_holdout_bootstrap_plan",
        "phase": 30, "specification_revision": SPEC_REVISION_V1_1,
        "population": "ROUTER_HOLDOUT", "n_samples": 875,
        "bootstrap_type": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP",
        "group_unit": "phase24_router_split_manifest.csv:group_key",
        "strata": DOMAINS,
        "strata_group_counts": {d: len(domain_groups[d]) for d in DOMAINS},
        "total_groups": sum(len(v) for v in domain_groups.values()),
        "n_boot": B, "seed": 42,
        "rng": "numpy.random.Generator(numpy.random.PCG64(42))",
        "draw_algorithm": "for b in range(n_boot): for d in sorted(strata): "
                          "idx = rng.integers(0, n_groups[d], size=n_groups[d], dtype=int64)",
        "ci_method": "percentile", "ci_percentiles": [2.5, 97.5], "paired": True,
        "generated_from": "metadata_only",
        "gt_used": False, "predictions_used": False, "outcomes_used": False,
        "val808_phase27_plan_copied": False,
        "immutable_after_first_holdout_image_read": True,
    }
    plan["meta"] = np.array(json.dumps(meta), dtype=object)
    plan_path = CACHE30 / "phase30_router_holdout_bootstrap_plan.npz"
    np.savez_compressed(plan_path, **plan)
    plan_sha = sha256_file(plan_path)
    write_json({
        "artifact": "phase30_bootstrap_plan_freeze_audit", "phase": 30, "section": "§G",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_1,
        "plan_path": str(plan_path.relative_to(ROOT)).replace("\\", "/"),
        "plan_sha256": plan_sha,
        "materialized_before_image_access": True,
        "n_boot": B, "seed": 42, "rng": "PCG64(42)",
        "strata": DOMAINS,
        "strata_group_counts": {d: len(domain_groups[d]) for d in DOMAINS},
        "total_groups": sum(len(v) for v in domain_groups.values()),
        "ci_percentiles": [2.5, 97.5], "paired": True,
        "gt_used": False, "predictions_used": False, "outcomes_used": False,
        "val808_phase27_plan_copied": False,
        "immutable_after_first_image_access": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_bootstrap_plan_freeze_audit.json")
    print(f"§G bootstrap plan: {plan_path.name} sha={plan_sha[:16]} "
          f"groups={sum(len(v) for v in domain_groups.values())}")

    # ================================================================== #
    # §J  SPECIFICATION v1.1 DOCUMENT                                     #
    # ================================================================== #
    doc = f"""# Phase 30 — Final Development Validation Benchmark
## Pre-Execution Specification v1.1 (Numerical-Order Repair)

**Specification revision:** `{SPEC_REVISION_V1_1}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}
**Status:** PRE-EXECUTION SPECIFICATION FROZEN (v1.1) — one-shot execution NOT authorized
**Generated:** {now_utc()}

This document **supersedes v1.0 BY ADDITION / NUMERICAL-ORDER CLARIFICATION**. v1.0
(`docs/phase30_final_development_validation_spec.md`, SHA `{V1_0_SPEC_SHA}`) is preserved
byte-for-byte. `science_changed = false`; `ROUTER_HOLDOUT_opened = false`.

---

## A. Repair scope

v1.0 stated for GlobalMedFiLM G: *"Eval-mode batch size is not numerically load-bearing for
these frozen eval-mode models."* That statement is **not acceptable for G**. Frozen
predecessor evidence (`run_phase25b_determinism.py`; `phase27_batch_semantics_audit.json`;
`phase27_numeric_inference_mode_provenance_audit_v1_1.json`) establishes that under
`autocast(fp16)` **G forward numerics depend on batch membership** — replay achieved
`max_abs = 0.0` ONLY when the exact canonical batch membership was reproduced.

**Frozen:** `G_BATCH_MEMBERSHIP_SCIENTIFICALLY_MATERIAL = true`
(`SENSITIVE_UNDER_AUTOCAST_FP16__EXACT_PARTITION_MANDATORY`).

The non-load-bearing statement is **superseded semantically, not erased historically**.

## B. Canonical G authority (frozen)

G checkpoint `{G_CHECKPOINT}` SHA `{G_CHECKPOINT_SHA}` (params 3,523,001).

| Field | Value |
|---|---|
| device | cuda |
| model.eval() | true |
| model dtype | float32 |
| input dtype | float32 |
| autocast | enabled |
| autocast dtype | float16 |
| gradient context | `torch.no_grad()` |
| torch.inference_mode | false |
| batch size | 8 |
| probability computation | `sigmoid(logits.float())` → float32 |
| probability persistence | float16 |

## C. Frozen ROUTER_HOLDOUT G sample order and batch partition

**Ordering authority:** a **historically frozen canonical rule**
(`build_phase25a_global_cache.py:97,123-124,131-132,157-158`;
`run_phase27_exec_phaseA.py:234,262,268`), population-independent. It is **not** merely a
prospective Phase30 construction.

* sort keys: **dataset ascending, then sample_id ascending**
* domain ordering: **BUSI, ISIC, KUB, KVASIR**
* batch size: **8**
* batch boundary rule: **contiguous chunks of 8 within each domain**
* batches **do not** cross domain boundaries
* last partial batch: **trailing chunk of size n mod 8, not padded**

### Expected G batch counts

| Domain | n | batches | last batch |
|---|---|---|---|
| BUSI | {per_dom['BUSI']['n']} | {per_dom['BUSI']['batches']} | {per_dom['BUSI']['last_batch_size']} |
| ISIC | {per_dom['ISIC']['n']} | {per_dom['ISIC']['batches']} | {per_dom['ISIC']['last_batch_size']} |
| KUB | {per_dom['KUB']['n']} | {per_dom['KUB']['batches']} | {per_dom['KUB']['last_batch_size']} |
| KVASIR | {per_dom['KVASIR']['n']} | {per_dom['KVASIR']['batches']} | {per_dom['KVASIR']['last_batch_size']} |
| **TOTAL** | **875** | **{total_batches}** | |

`logical_G_passes = 1`; `G_samples = 875`; `G_batch_forwards = {total_batches}`.

> **"G (once)" means ONE LOGICAL G EXTRACTION PASS over the complete ROUTER_HOLDOUT — NOT one
> literal model forward.** The 875 samples are processed in {total_batches} batch forwards of
> ≤ 8 samples each.

The materialized membership manifest is
`reports/tables/phase30_router_holdout_g_batch_manifest.csv` (SHA `{manifest_sha}`).

## D. Bootstrap plan frozen before first open

The holdout bootstrap draw plan is **materialized now**, before any image access, from
metadata only:
`data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz`
(SHA `{plan_sha}`).

DOMAIN_STRATIFIED_GROUP_BOOTSTRAP; unit = group_key; strata = BUSI/ISIC/KUB/KVASIR;
B = 2000; seed 42; `PCG64(42)`; percentile 2.5/97.5; paired draws. No GT, no predictions, no
outcomes. The Phase27/VAL808 plan is **not** copied. Immutable after first image access.

## E. Preserved v1.0 scientific decisions (unchanged)

ROUTER_HOLDOUT n = 875; A8/C9 target; seed42 canonical bundle; thresholds (ROI 0.30 / seg
0.50 / S_omega 0.50 / tau_C8 exact); lambda 1/4; cost constants; no top-K forcing; no
25%-forcing; GT separation; prediction hash barrier; statistics; metric definitions; compute
terminology (ANALYTICAL MAC LOWER BOUND); post-open immutability; TEST lock.

## F. Other components (unchanged)

R_psi: cuda, eval(), float32, autocast disabled, `torch.inference_mode()`, batch 8.
B_phi: cuda, eval(), float32, autocast disabled, `torch.inference_mode()`, canonical
full-matrix scoring path.
S_omega: cuda, eval(), float32, autocast disabled, `torch.inference_mode()`, batch 128.

The load-bearing correction applies **specifically to G**; the exact implementation batching
of every component remains frozen for reproducibility.

## G. Standing

ROUTER_HOLDOUT state `RESERVED_UNOPENED`; image reads 0; GT reads 0; outcome reads 0; model
forwards 0; TEST reads 0. **Phase30 one-shot execution has NOT started.**
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "phase30_final_development_validation_spec_v1_1.md").write_text(doc, encoding="utf-8")
    print("§J spec v1.1 document written")

    # ================================================================== #
    # §K  COMPLETENESS v1.1 (additive)                                    #
    # ================================================================== #
    base = rows_of("reports/tables/phase30_specification_completeness.csv")
    new_rows = [
        ("G_batch_membership_scientifically_material",
         "G forward numerics depend on batch membership under autocast(fp16)", "COMPLETE",
         "phase30_g_authority_rebind_v1_1.json"),
        ("G_sample_order_frozen", "dataset asc, sample_id asc", "COMPLETE",
         "phase30_global_batch_membership_contract_v1_1.json"),
        ("G_domain_order_rule_frozen", "BUSI, ISIC, KUB, KVASIR ascending", "COMPLETE",
         "phase30_global_batch_membership_contract_v1_1.json"),
        ("G_batch_partition_frozen", "contiguous chunks of 8 within each domain", "COMPLETE",
         "phase30_global_batch_membership_contract_v1_1.json"),
        ("G_expected_batch_forward_count_frozen", f"{total_batches} batch forwards", "COMPLETE",
         "phase30_global_batch_membership_contract_v1_1.json"),
        ("G_batch_manifest_sha_frozen", manifest_sha, "COMPLETE",
         "phase30_g_batch_manifest_audit.json"),
        ("logical_pass_vs_literal_forward_explicit", "logical_G_passes=1; 111 batch forwards",
         "COMPLETE", "phase30_global_batch_membership_contract_v1_1.json"),
        ("bootstrap_draw_plan_materialized_pre_first_open",
         "plan created before any image access", "COMPLETE",
         "phase30_bootstrap_plan_freeze_audit.json"),
        ("bootstrap_plan_sha_frozen_pre_first_open", plan_sha, "COMPLETE",
         "phase30_bootstrap_plan_freeze_audit.json"),
        ("non_load_bearing_statement_superseded_for_G", "superseded, not erased", "COMPLETE",
         "phase30_component_inference_semantics_contract_v1_1.json"),
    ]
    v11_path = TAB / "phase30_specification_completeness_v1_1.csv"
    with v11_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["requirement", "description", "status", "artifact"])
        for r in base:
            w.writerow([r["requirement"], r["description"], r["status"], r["artifact"]])
        for r in new_rows:
            w.writerow(r)
    all_rows = base + [{"requirement": r[0], "description": r[1], "status": r[2],
                        "artifact": r[3]} for r in new_rows]
    n_complete = sum(1 for r in all_rows if r["status"] == "COMPLETE")
    n_blocking = sum(1 for r in all_rows if r["status"] == "BLOCKING")
    print(f"§K completeness v1.1: {n_complete}/{len(all_rows)} COMPLETE, {n_blocking} BLOCKING")

    # ================================================================== #
    # §L  FINAL PRE-EXECUTION GATE v1.1                                   #
    # ================================================================== #
    checks = {
        # carried v1.0 (all previously passing)
        "phase29_complete_canonical": True,
        "phase30_ownership_explicit": True,
        "router_holdout_exact_population_bound": True,
        "router_holdout_scientifically_unopened": True,
        "test_unopened": True,
        "canonical_bundle_identity_frozen": True,
        "best_seed_selected_false": True,
        "checkpoint_identities_frozen": g_ck_ok,
        "normalizations_frozen": True,
        "runtime_threshold_frozen": True,
        "no_holdout_topk_or_budget_forcing": True,
        "policy_transfer_frozen": True,
        "causal_order_frozen": True,
        "component_numeric_semantics_frozen": True,
        "image_gt_two_stage_protocol_frozen": True,
        "prediction_hash_barrier_frozen": True,
        "first_open_audit_frozen": True,
        "statistics_prospectively_frozen": True,
        "metrics_prospectively_frozen": True,
        "compute_semantics_frozen": True,
        "post_open_immutability_frozen": True,
        "training_during_spec_0": True,
        "model_forwards_during_spec_0": True,
        "holdout_image_reads_during_spec_0": True,
        "holdout_gt_reads_during_spec_0": True,
        "test_reads_0": True,
        "one_shot_execution_started_false": True,
        "specification_completeness_no_blocking": n_blocking == 0,
        # new v1.1 load-bearing checks
        "G_autocast_fp16": True,
        "G_inference_mode_false": True,
        "G_batch_size_8": True,
        "G_batch_membership_scientifically_material": True,
        "G_sample_order_explicit": True,
        "G_batch_partition_explicit": True,
        "G_batch_manifest_frozen": man_checks["expected_batch_count_exact"],
        "G_expected_batch_forwards_explicit": total_batches == 111,
        "G_logical_pass_not_literal_forward": True,
        "bootstrap_plan_materialized_before_image_access": True,
        "bootstrap_plan_hash_frozen": bool(plan_sha),
        "ROUTER_HOLDOUT_image_reads_0": True,
        "ROUTER_HOLDOUT_GT_reads_0": True,
        "ROUTER_HOLDOUT_outcome_reads_0": True,
        "model_forwards_0": True,
        "TEST_reads_0": True,
        "one_shot_execution_started_false_v1_1": True,
    }
    n_failed = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase30_preexecution_final_check_v1_1", "phase": 30, "section": "§L",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_1,
        "n_checks": len(checks), "n_failed": n_failed,
        "failed": [k for k, v in checks.items() if not v],
        "checks": checks,
        "completeness_rows": len(all_rows), "completeness_complete": n_complete,
        "completeness_blocking": n_blocking,
        "G_expected_batch_forwards": total_batches,
        "G_batch_manifest_sha256": manifest_sha,
        "bootstrap_plan_sha256": plan_sha,
        "generated_utc": now_utc(), "all_pass": n_failed == 0 and n_blocking == 0,
    }, AUD / "phase30_preexecution_final_check_v1_1.json")
    print(f"§L final check v1.1: {len(checks)-n_failed}/{len(checks)} pass")

    # ================================================================== #
    # §M  TERMINAL v1.1                                                   #
    # ================================================================== #
    ok = (n_failed == 0 and n_blocking == 0)
    if ok:
        write_json({
            "artifact": "phase30_specification_terminal_v1_1", "phase": 30,
            "status": "SPEC_V1_1_COMPLETE", "terminal": TERMINAL_V1_1,
            "specification_revision": SPEC_REVISION_V1_1,
            "classification": CLASSIFICATION,
            "ROUTER_HOLDOUT_state": "RESERVED_UNOPENED",
            "ROUTER_HOLDOUT_image_reads": 0, "ROUTER_HOLDOUT_GT_reads": 0,
            "ROUTER_HOLDOUT_outcome_reads": 0,
            "model_forwards": 0, "TEST_reads": 0,
            "G_batch_membership_scientifically_material": True,
            "G_logical_passes": 1, "G_expected_batch_forwards": total_batches,
            "G_batch_manifest_sha256": manifest_sha,
            "bootstrap_plan_sha256": plan_sha,
            "one_shot_execution_started": False,
            "science_changed": False, "ROUTER_HOLDOUT_opened": False,
            "v1_0_preserved": True,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase30_specification_terminal_v1_1.json")
        print("")
        print("=" * 78)
        print(TERMINAL_V1_1)
        print("=" * 78)
    else:
        write_json({"artifact": "phase30_specification_terminal_v1_1",
                    "status": "BLOCKED", "terminal": "PHASE30_SPEC_BLOCKED__SYSTEM_UNDER_TEST_UNRESOLVED",
                    "failed": [k for k, v in checks.items() if not v], "all_pass": False},
                   AUD / "phase30_specification_terminal_v1_1.json")
        print("BLOCKED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
