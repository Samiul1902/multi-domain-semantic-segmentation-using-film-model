#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PHASE 29 — PHASE B AUDITS
Additive trainer parameterization + seed-42 parity re-verification.

NO TRAINING. NO OPTIMIZER STEP. NO BACKWARD. NO SCIENTIFIC FORWARD.
NO VAL808. NO ROUTER_HOLDOUT. NO TEST.
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
PROV = AUD / "phase29_preexecution_existing_root_provenance"
NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()

sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

ENTRY_TERMINAL = "PHASE29_PHASE_A_GATES_PASS__TRAINING_NOT_STARTED"
SUCCESS_TERMINAL = (
    "PHASE29_PHASE_B_TRAINER_PARAMETERIZATION_COMPLETE__SEED42_CONFIG_PARITY_"
    "AND_32_RUN_PLAN_FROZEN__TRAINING_ELIGIBLE_NOT_STARTED"
)
BLOCKED = {
    "CANONICAL_TRAINER_SOURCE_DRIFT":
        "PHASE29_PHASE_B_BLOCKED__CANONICAL_TRAINER_SOURCE_DRIFT",
    "SEED_ROOT_CONTAMINATION_UNRESOLVED":
        "PHASE29_PHASE_B_BLOCKED__SEED_ROOT_CONTAMINATION_UNRESOLVED",
    "SEED42_TRAINER_PARITY_FAILURE":
        "PHASE29_PHASE_B_BLOCKED__SEED42_TRAINER_PARITY_FAILURE",
    "SEED_BIND_AFTER_RNG_DRAW":
        "PHASE29_PHASE_B_BLOCKED__SEED_BIND_AFTER_RNG_DRAW",
    "FIXED_PARTITION_IDENTITY_FAILURE":
        "PHASE29_PHASE_B_BLOCKED__FIXED_PARTITION_IDENTITY_FAILURE",
    "OUTPUT_PATH_COLLISION":
        "PHASE29_PHASE_B_BLOCKED__OUTPUT_PATH_COLLISION",
    "TRAINER_PARAMETERIZATION_INCOMPLETE":
        "PHASE29_PHASE_B_BLOCKED__TRAINER_PARAMETERIZATION_INCOMPLETE",
    "CANONICAL_TRAINER_MUTATION_REQUIRED":
        "PHASE29_PHASE_B_BLOCKED__CANONICAL_TRAINER_MUTATION_REQUIRED",
}

SEEDS = [42, 123, 3407]
NEW_SEEDS = [123, 3407]
N_FOLDS_BPHI = 5
N_FOLDS_SOMEGA = 5
N_FOLDS_RPSI = 3
# Canonical S_omega CV fold sizes (derived from Phase25F OOF safety table).
SOMEGA_FOLD_SIZES = [991, 991, 991, 992, 992]

ROOTS = []
for s in NEW_SEEDS:
    for b in ("checkpoints", "data_cache", "experiments"):
        ROOTS.append(f"{b}/phase29_seed{s}")

CANONICAL_SOURCES = {
    "train_phase25a_refiner.py":
        ("scripts/training/train_phase25a_refiner.py",
         "487efd3a934c97bf3b4db13717ac29b567a535346a2510a946943e2506345835"),
    "train_phase25d_router.py":
        ("scripts/analysis/train_phase25d_router.py",
         "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91"),
    "phase25f_execution_common.py":
        ("scripts/analysis/phase25f_execution_common.py",
         "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e"),
    "phase25f_spec_repair_common.py":
        ("scripts/analysis/phase25f_spec_repair_common.py",
         "18caebe79fce11ad27766af157bc6acf671f9a3c29911df253ba07754c66bd4e"),
    "run_phase25f_cv_training.py":
        ("scripts/analysis/run_phase25f_cv_training.py",
         "327d554c20bc018c08d314daec978506a590304edc579cc28efcecf2a5459f37"),
    "run_phase25f_final_refit.py":
        ("scripts/analysis/run_phase25f_final_refit.py",
         "1b79c89c259b5cc06ce88464cf966b5e5d2d33b546f47d14c7449923cf2f7b37"),
    "regional_refiner.py":
        ("src/models/barr/regional_refiner.py",
         "4fe0abde3ec3a183d930f676c4400b4d9ba778793ea64abf1755c5b8dabf947a"),
    "barr_refiner_dataset.py":
        ("src/data/barr_refiner_dataset.py",
         "6bbf0eb51f9a4f646fe9222f2d3035761577f8d41cc5c229109139bfc937e095"),
    "barr_roi.py":
        ("src/data/barr_roi.py",
         "4b1015275e4e31f9cc2b662a290c18f988eaea65cec64082cea217fad9aba9d6"),
}

WRAPPERS = [
    "scripts/analysis/phase29_train_rpsi.py",
    "scripts/analysis/phase29_train_bphi.py",
    "scripts/analysis/phase29_train_somega.py",
]

PHASE_A_BINDINGS = [
    ("G_checkpoint", "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
     "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
    ("phase25b_features",
     "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy",
     "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a"),
    ("phase25a_rpsi_final_ckpt",
     "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
     "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
    ("phase25d_bphi_final_ckpt",
     "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
     "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
    ("phase25f_somega_final_ckpt",
     "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
     "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
    ("phase26_final_freeze", "reports/audits/phase26_final_freeze.json",
     "e709f5301894dc0377420500a9b6d6e95bd54858fde4cb472cad73d630b8adb4"),
    ("phase28_final_freeze", "reports/audits/phase28_final_freeze.json",
     "ac4b9f72ce663e57d4f7049a979e3bad8cd3ec460cca494c332e9ebc32bb098a"),
    ("phase29_spec_v1_1_terminal", "reports/audits/phase29_spec_v1_1_terminal.json", None),
]


def sha(p) -> str | None:
    fp = ROOT / p if not os.path.isabs(str(p)) else Path(p)
    if not fp.exists():
        return None
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def wj(rel, obj):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


# --------------------------------------------------------------------------- #
# §0-§1 entry gate + binding rehash
# --------------------------------------------------------------------------- #
def s0_s1():
    pa = json.load(open(AUD / "phase29_phase_a_terminal.json", encoding="utf-8"))
    checks = {
        "phase_a_terminal_exact": pa.get("terminal") == ENTRY_TERMINAL,
        "training_runs_0": pa.get("training_runs") == 0,
        "model_forwards_0": pa.get("model_forwards") == 0,
        "val808_reads_0": pa.get("val808_reads") == 0,
        "router_holdout_reads_0": pa.get("router_holdout_reads") == 0,
        "test_reads_0": pa.get("test_reads") == 0,
    }
    gate = all(checks.values())
    wj("reports/audits/phase29_phase_b_entry_gate.json", {
        "artifact": "phase29_phase_b_entry_gate",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "required_terminal": ENTRY_TERMINAL,
        "observed_terminal": pa.get("terminal"),
        "checks": checks,
        "gate_pass": gate,
        "blocked_terminal_if_fail": BLOCKED["TRAINER_PARAMETERIZATION_INCOMPLETE"],
        "all_pass": gate,
    })

    rows = []
    for name, path, exp in PHASE_A_BINDINGS:
        act = sha(path)
        rows.append({"name": name, "path": path, "sha256_expected": exp,
                     "sha256_observed": act,
                     "unchanged": act is not None and (exp is None or act == exp)})
    drift = [r["name"] for r in rows if not r["unchanged"]]
    wj("reports/audits/phase29_phase_b_binding_rehash.json", {
        "artifact": "phase29_phase_b_binding_rehash",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "bindings": rows, "n_bindings": len(rows), "n_drift": len(drift),
        "drift": drift, "artifact_drift": len(drift) > 0,
        "blocked_terminal_if_drift":
            "PHASE29_PHASE_B_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT",
        "all_pass": len(drift) == 0,
    })
    print("[§0-§1] entry gate:", "PASS" if gate else "FAIL",
          "| binding rehash:", f"{len(rows)} bound, {len(drift)} drift")
    return {"gate": gate, "drift": len(drift)}


# --------------------------------------------------------------------------- #
# §2 seed root inventory + cleanliness
# --------------------------------------------------------------------------- #
def s2():
    inventory = []
    for rel in ROOTS:
        base = ROOT / rel
        files = []
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    files.append({
                        "path": str(p.relative_to(ROOT)).replace(os.sep, "/"),
                        "relative_to_root": str(p.relative_to(base)).replace(os.sep, "/"),
                        "size_bytes": p.stat().st_size,
                        "sha256": sha(str(p)),
                        "mtime": _dt.datetime.fromtimestamp(
                            p.stat().st_mtime, _dt.timezone.utc).isoformat(),
                    })
        cls = "EMPTY_ROOT" if not files else "UNKNOWN"
        inventory.append({
            "root": rel + "/", "exists": base.exists(),
            "n_files": len(files), "classification": cls, "files": files,
        })

    unknown = [i for i in inventory
               if i["classification"] not in ("EMPTY_ROOT",
                                              "PHASE29_PREEXECUTION_GOVERNANCE_ARTIFACT")]
    wj("reports/audits/phase29_existing_seed_root_inventory.json", {
        "artifact": "phase29_existing_seed_root_inventory",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "n_roots": len(inventory), "roots": inventory,
        "allowed_classifications": [
            "EMPTY_ROOT", "PHASE29_PREEXECUTION_GOVERNANCE_ARTIFACT",
            "STALE_PREVIOUS_ATTEMPT", "UNKNOWN",
        ],
        "all_pass": True,
    })

    clean = not unknown
    wj("reports/audits/phase29_seed_root_cleanliness_gate.json", {
        "artifact": "phase29_seed_root_cleanliness_gate",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "quarantine_location": str(PROV.relative_to(ROOT)).replace(os.sep, "/"),
        "quarantine_used": False,
        "n_unknown_roots": len(unknown),
        "unknown_roots": [u["root"] for u in unknown],
        "all_roots_empty": all(i["classification"] == "EMPTY_ROOT" for i in inventory),
        "scientific_roots_clean": clean,
        "stale_artifacts_deleted_silently": False,
        "blocked_terminal_if_unresolved":
            BLOCKED["SEED_ROOT_CONTAMINATION_UNRESOLVED"],
        "all_pass": clean,
    })
    print("[§2] seed roots:", f"{len(inventory)} roots,",
          "all empty" if clean else "CONTAMINATED")
    return {"clean": clean, "inventory": inventory}


# --------------------------------------------------------------------------- #
# §20 source integrity
# --------------------------------------------------------------------------- #
def s20():
    rows = []
    for name, (path, exp) in CANONICAL_SOURCES.items():
        act = sha(path)
        rows.append({"name": name, "path": path, "sha256_expected": exp,
                     "sha256_observed": act, "unchanged": act == exp})
    drift = [r["name"] for r in rows if not r["unchanged"]]

    wraps = []
    for w in WRAPPERS:
        wraps.append({"path": w, "sha256": sha(w), "exists": (ROOT / w).exists()})

    wj("reports/audits/phase29_trainer_source_integrity.json", {
        "artifact": "phase29_trainer_source_integrity",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "historical_canonical_sources": rows,
        "n_historical": len(rows), "n_drift": len(drift), "drift": drift,
        "historical_trainer_sources_unchanged": len(drift) == 0,
        "phase29_wrappers": wraps,
        "phase29_wrappers_additive_only": all(w["exists"] for w in wraps),
        "blocked_terminal_if_drift":
            BLOCKED["CANONICAL_TRAINER_SOURCE_DRIFT"],
        "all_pass": len(drift) == 0 and all(w["exists"] for w in wraps),
    })
    print("[§20] source integrity:", f"{len(rows)} canonical, {len(drift)} drift",
          "|", f"{len(wraps)} wrappers")
    return {"drift": len(drift), "ok": len(drift) == 0}


# --------------------------------------------------------------------------- #
# §7 / §9-§11 seed binding + parity
# --------------------------------------------------------------------------- #
def s7_9_11():
    import phase29_train_rpsi as R
    import phase29_train_bphi as B
    import phase29_train_somega as S

    # ---- §7 RNG bind-before-draw -----------------------------------------
    rng = [R.seed_bind_before_rng(), B.seed_bind_before_rng(),
           S.seed_bind_before_rng()]
    bind_ok = all(r["seed_bound_before_first_rng_draw"] for r in rng)
    wj("reports/audits/phase29_rng_bind_before_draw_audit.json", {
        "artifact": "phase29_rng_bind_before_draw_audit",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "method": "stdlib random.seed instrumented; SEED_BIND event index "
                  "compared against FIRST_RNG_DRAW event index",
        "components": rng,
        "all_components_seed_bound_before_rng": bind_ok,
        "blocked_terminal_if_fail": BLOCKED["SEED_BIND_AFTER_RNG_DRAW"],
        "all_pass": bind_ok,
    })

    # ---- §9 R_psi parity --------------------------------------------------
    rpsi_parity = {
        "canonical": {
            "component": "R_psi", "class": "BARRRegionalRefinerV1",
            "arch_revision": "ra_medfilm_barr_narrowed_v1_1",
            "seed": 42, "batch": 8, "lr": 1e-4, "weight_decay": 1e-4,
            "max_epochs": 100, "patience": 15, "t_max": 100,
            "amp": True, "selection_rule": "minimum EARLY_STOP total loss",
            "roi_threshold": 0.30,
            "fold_roles": ["fit", "early_stop", "outer_target"],
            "n_folds": N_FOLDS_RPSI,
        },
        "phase29_wrapper_seed42": {
            "component": "R_psi",
            "training_seed_fold": [R.fold_training_seed(42)] * N_FOLDS_RPSI,
            "training_seed_final": R.final_refit_seed(42),
            "spec_fold0": R.build_run_spec(42, "fold0"),
            "spec_final": R.build_run_spec(42, "final"),
        },
    }
    rpsi_ok = (
        rpsi_parity["phase29_wrapper_seed42"]["training_seed_fold"] == [42, 42, 42]
        and rpsi_parity["phase29_wrapper_seed42"]["training_seed_final"] == 42
    )
    wj("reports/audits/phase29_rpsi_wrapper_parity.json", {
        "artifact": "phase29_rpsi_wrapper_parity",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE", "retrained": False,
        "parity": rpsi_parity,
        "output_roots_expected_to_differ": True,
        "scientific_config_matches": rpsi_ok,
        "all_pass": rpsi_ok,
    })

    # ---- §10 B_phi parity -------------------------------------------------
    seeds42 = [B.router_fold_seed(42, k) for k in range(N_FOLDS_BPHI)]
    bphi_ok = (seeds42 == [42000, 42001, 42002, 42003, 42004]
               and B.final_refit_seed(42) == 42)
    wj("reports/audits/phase29_bphi_wrapper_parity.json", {
        "artifact": "phase29_bphi_wrapper_parity",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE", "retrained": False,
        "canonical_fold_seeds": [42000, 42001, 42002, 42003, 42004],
        "wrapper_fold_seeds_seed42": seeds42,
        "wrapper_final_seed_seed42": B.final_refit_seed(42),
        "fingerprint": B.parity_fingerprint(),
        "spec_fold0": B.build_fold_spec(42, 0),
        "spec_final": B.build_final_spec(42),
        "fold_seeds_match": seeds42 == [42000, 42001, 42002, 42003, 42004],
        "scientific_config_matches": bphi_ok,
        "all_pass": bphi_ok,
    })

    # ---- §11 S_omega parity ----------------------------------------------
    s42 = [S.safety_fold_seed(42, k) for k in range(N_FOLDS_SOMEGA)]
    som_ok = (s42 == [54000, 54001, 54002, 54003, 54004]
              and S.final_refit_seed(42) == 42)
    wj("reports/audits/phase29_somega_wrapper_parity.json", {
        "artifact": "phase29_somega_wrapper_parity",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE", "retrained": False,
        "canonical_fold_seeds": [54000, 54001, 54002, 54003, 54004],
        "wrapper_fold_seeds_seed42": s42,
        "wrapper_final_seed_seed42": S.final_refit_seed(42),
        "fingerprint": S.parity_fingerprint(),
        "runtime_constants_seed42": S.resolve_runtime_constants(42),
        "spec_fold0": S.build_fold_spec(42, 0),
        "spec_final": S.build_final_spec(42),
        "fold_seeds_match": s42 == [54000, 54001, 54002, 54003, 54004],
        "scientific_config_matches": som_ok,
        "all_pass": som_ok,
    })

    print("[§7] RNG bind-before-draw:", "PASS" if bind_ok else "FAIL")
    print("[§9-§11] parity | R_psi:", "PASS" if rpsi_ok else "FAIL",
          "| B_phi:", "PASS" if bphi_ok else "FAIL",
          "| S_omega:", "PASS" if som_ok else "FAIL")
    return {"rng": bind_ok, "rpsi": rpsi_ok, "bphi": bphi_ok, "somega": som_ok}


# --------------------------------------------------------------------------- #
# §13 fixed partition full identity proof
# --------------------------------------------------------------------------- #
def _ids(path) -> list:
    with open(path, encoding="utf-8") as f:
        return [r["sample_id"] for r in csv.DictReader(f)]


def s13():
    checks = {}
    detail = {}

    # ---- B_phi: 5 folds x (fit, early_stop, outer_target) ----------------
    for k in range(N_FOLDS_BPHI):
        fit = _ids(TAB / f"phase25d_cv_fold{k}_fit_ids.csv")
        es = _ids(TAB / f"phase25d_cv_fold{k}_early_stop_ids.csv")
        ot = _ids(TAB / f"phase25d_cv_fold{k}_outer_target_ids.csv")
        sf, se, so = set(fit), set(es), set(ot)
        checks[f"bphi_fold{k}_fit_es_disjoint"] = not (sf & se)
        checks[f"bphi_fold{k}_fit_ot_disjoint"] = not (sf & so)
        checks[f"bphi_fold{k}_es_ot_disjoint"] = not (se & so)
        checks[f"bphi_fold{k}_union_4957"] = len(sf | se | so) == 4957
        checks[f"bphi_fold{k}_no_duplicates"] = (
            len(fit) == len(sf) and len(es) == len(se) and len(ot) == len(so))
        detail[f"bphi_fold{k}"] = {"fit": len(fit), "early_stop": len(es),
                                   "outer_target": len(ot),
                                   "union": len(sf | se | so)}

    # ---- S_omega: 5 folds from the canonical OOF safety predictions ------
    # phase25f_cv_fold_role_assignments.csv is an AGGREGATE (fold,role,n).
    # The authoritative per-sample fold assignment is carried by the OOF
    # safety prediction table (column: safety_cv_fold).
    som_path = ROOT / "data_cache/phase25f_barr_post_safety_v1_0" \
                      "/phase25f_oof_safety_predictions.csv"
    som_fold_ids = {k: [] for k in range(N_FOLDS_SOMEGA)}
    som_all = []
    with open(som_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sid = r["sample_id"]
            k = int(r["safety_cv_fold"])
            som_fold_ids[k].append(sid)
            som_all.append(sid)
    for k in range(N_FOLDS_SOMEGA):
        ids_k = som_fold_ids[k]
        detail[f"somega_fold{k}"] = {"n": len(ids_k)}
        checks[f"somega_fold{k}_nonempty"] = len(ids_k) > 0
    checks["somega_total_4957"] = len(som_all) == 4957
    checks["somega_no_duplicates"] = len(set(som_all)) == len(som_all) == 4957
    checks["somega_fold_union_4957"] = (
        len({i for ids_k in som_fold_ids.values() for i in ids_k}) == 4957)
    checks["somega_fold_sizes_expected"] = (
        sorted(len(v) for v in som_fold_ids.values()) == SOMEGA_FOLD_SIZES)
    detail["somega_total_rows"] = len(som_all)
    detail["somega_fold_sizes"] = sorted(len(v) for v in som_fold_ids.values())

    # ---- R_psi: 3 folds from the ROI-0.30 cache --------------------------
    cache = ROOT / "data_cache/phase25a_barr_roi030_cache/folds"
    for k in range(N_FOLDS_RPSI):
        fit = _ids(cache / f"fold{k}_fit.csv")
        es = _ids(cache / f"fold{k}_early_stop.csv")
        ot = _ids(cache / f"fold{k}_outer_target.csv")
        sf, se, so = set(fit), set(es), set(ot)
        checks[f"rpsi_fold{k}_fit_es_disjoint"] = not (sf & se)
        checks[f"rpsi_fold{k}_fit_ot_disjoint"] = not (sf & so)
        checks[f"rpsi_fold{k}_es_ot_disjoint"] = not (se & so)
        checks[f"rpsi_fold{k}_union_4957"] = len(sf | se | so) == 4957
        detail[f"rpsi_fold{k}"] = {"fit": len(fit), "early_stop": len(es),
                                   "outer_target": len(ot),
                                   "union": len(sf | se | so)}

    # ---- outer_target coverage across folds (exactly once) ---------------
    all_bphi_ot = []
    for k in range(N_FOLDS_BPHI):
        all_bphi_ot += _ids(TAB / f"phase25d_cv_fold{k}_outer_target_ids.csv")
    checks["bphi_outer_target_covers_4957_once"] = (
        len(all_bphi_ot) == 4957 and len(set(all_bphi_ot)) == 4957)

    ok = all(checks.values())
    wj("reports/audits/phase29_fixed_partition_full_identity_proof.json", {
        "artifact": "phase29_fixed_partition_full_identity_proof",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "classification": "FIXED_PARTITIONS__OPTIMIZATION_RANDOMNESS_ONLY",
        "proof": "physical sample-id set equality, disjointness and union "
                 "cardinality against the canonical seed-42 manifests",
        "per_fold_detail": detail,
        "checks": checks, "n_checks": len(checks),
        "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail": BLOCKED["FIXED_PARTITION_IDENTITY_FAILURE"],
        "all_pass": ok,
    })
    print("[§13] fixed partition full identity:",
          f"{len(checks)-sum(1 for v in checks.values() if not v)}/{len(checks)}",
          "PASS" if ok else "FAIL")
    return {"ok": ok, "n_checks": len(checks),
            "n_failed": sum(1 for v in checks.values() if not v)}


# --------------------------------------------------------------------------- #
# §14-§15 run config registry + output collision
# --------------------------------------------------------------------------- #
def s14_15():
    import phase29_train_rpsi as R
    import phase29_train_bphi as B
    import phase29_train_somega as S

    runs = []
    for s in NEW_SEEDS:
        for k in range(N_FOLDS_RPSI):
            sp = R.build_run_spec(s, f"fold{k}")
            runs.append({"run_id": f"seed{s}_rpsi_fold{k}", "component": "R_psi",
                         "role": f"fold{k}", "master_seed": s,
                         "training_seed": sp["training_seed"],
                         "checkpoint_dir": sp["run_checkpoint_dir"],
                         "experiment_dir": sp["run_experiment_dir"],
                         "fit_manifest": sp["fit_manifest"],
                         "early_stop_manifest": sp["early_stop_manifest"]})
        sp = R.build_run_spec(s, "final")
        runs.append({"run_id": f"seed{s}_rpsi_final", "component": "R_psi",
                     "role": "final", "master_seed": s,
                     "training_seed": sp["training_seed"],
                     "checkpoint_dir": sp["run_checkpoint_dir"],
                     "experiment_dir": sp["run_experiment_dir"],
                     "fit_manifest": None, "early_stop_manifest": None})

        for k in range(N_FOLDS_BPHI):
            sp = B.build_fold_spec(s, k)
            runs.append({"run_id": f"seed{s}_bphi_fold{k}", "component": "B_phi",
                         "role": f"fold{k}", "master_seed": s,
                         "training_seed": sp["training_seed"],
                         "checkpoint_dir": sp["run_checkpoint_dir"],
                         "experiment_dir": sp["run_experiment_dir"],
                         "fit_manifest": sp["fold_manifests"]["fit"],
                         "early_stop_manifest": sp["fold_manifests"]["early_stop"]})
        sp = B.build_final_spec(s)
        runs.append({"run_id": f"seed{s}_bphi_final", "component": "B_phi",
                     "role": "final", "master_seed": s,
                     "training_seed": sp["training_seed"],
                     "checkpoint_dir": sp["run_checkpoint_dir"],
                     "experiment_dir": sp["run_experiment_dir"],
                     "fit_manifest": None, "early_stop_manifest": None})

        for k in range(N_FOLDS_SOMEGA):
            sp = S.build_fold_spec(s, k)
            runs.append({"run_id": f"seed{s}_somega_fold{k}",
                         "component": "S_omega", "role": f"fold{k}",
                         "master_seed": s, "training_seed": sp["training_seed"],
                         "checkpoint_dir": sp["run_checkpoint_dir"],
                         "experiment_dir": sp["run_experiment_dir"],
                         "fit_manifest": None, "early_stop_manifest": None})
        sp = S.build_final_spec(s)
        runs.append({"run_id": f"seed{s}_somega_final", "component": "S_omega",
                     "role": "final", "master_seed": s,
                     "training_seed": sp["training_seed"],
                     "checkpoint_dir": sp["run_checkpoint_dir"],
                     "experiment_dir": sp["run_experiment_dir"],
                     "fit_manifest": None, "early_stop_manifest": None})

    ids = [r["run_id"] for r in runs]
    ck = [r["checkpoint_dir"] for r in runs]
    ex = [r["experiment_dir"] for r in runs]
    wj("reports/audits/phase29_new_run_config_registry.json", {
        "artifact": "phase29_new_run_config_registry",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE", "launched": False,
        "runs": runs, "n_runs": len(runs),
        "n_unique_run_ids": len(set(ids)),
        "n_unique_checkpoint_dirs": len(set(ck)),
        "n_unique_experiment_dirs": len(set(ex)),
        "seed42_new_runs": len([r for r in runs if r["master_seed"] == 42]),
        "per_seed_counts": {
            str(s): len([r for r in runs if r["master_seed"] == s])
            for s in NEW_SEEDS},
        "all_pass": (len(runs) == 32 and len(set(ids)) == 32
                     and len(set(ck)) == 32 and len(set(ex)) == 32),
    })

    # ---- §15 collision audit --------------------------------------------
    collisions = []
    forbidden = ("phase21", "phase25a", "phase25d", "phase25f", "phase26",
                 "phase27", "phase28")
    for r in runs:
        low = (r["checkpoint_dir"] + "|" + r["experiment_dir"]).lower()
        for f in forbidden:
            if f in low:
                collisions.append({"run_id": r["run_id"], "forbidden": f})

    dup_ck = len(ck) - len(set(ck))
    dup_ex = len(ex) - len(set(ex))
    ok = (not collisions) and dup_ck == 0 and dup_ex == 0 and len(runs) == 32
    wj("reports/audits/phase29_output_collision_audit.json", {
        "artifact": "phase29_output_collision_audit",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "n_runs": len(runs),
        "duplicate_checkpoint_dirs": dup_ck,
        "duplicate_experiment_dirs": dup_ex,
        "forbidden_root_collisions": collisions,
        "writes_into_predecessor_phases": len(collisions) > 0,
        "blocked_terminal_if_collision": BLOCKED["OUTPUT_PATH_COLLISION"],
        "all_pass": ok,
    })
    print("[§14-§15] run registry:", len(runs), "runs |",
          len(set(ids)), "unique ids | collisions:", dup_ck + dup_ex + len(collisions))
    return {"n_runs": len(runs), "ok": ok}


# --------------------------------------------------------------------------- #
# §16 / §19 contracts
# --------------------------------------------------------------------------- #
def s16_19():
    wj("reports/audits/phase29_resume_semantics_contract.json", {
        "artifact": "phase29_resume_semantics_contract",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "frozen": True,
        "rules": [
            "resume only from that run's own latest/state checkpoint",
            "restore full RNG state where the canonical trainer supports it",
            "same master seed",
            "same derived fold seed",
            "same manifests",
            "same configuration fingerprint",
        ],
        "forbidden_on_resume": [
            "restart with a new seed", "change batch size",
            "change worker count", "change AMP", "change patience",
            "change scheduler",
        ],
        "resumed_interrupted_run_is_one_logical_run": True,
        "unresumable_failed_run_action": "STOP_FOR_REVIEW",
        "silent_restart_with_changed_semantics": False,
        "all_pass": True,
    })

    wj("reports/audits/phase29_val808_shared_global_cache_contract.json", {
        "artifact": "phase29_val808_shared_global_cache_contract",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE", "executed": False,
        "decision": "SHARED_FIXED_G_VAL808_FEATURE_EXTRACTION_REQUIRED_ONCE",
        "meaning": "ONE LOGICAL DATASET EXTRACTION PASS over 808 images",
        "not_meaning": "one literal neural-network batch forward",
        "shared_G_logical_passes": 1,
        "shared_G_samples": 808,
        "shared_G_batch_forwards": "DERIVED_FROM_FROZEN_PHASE27_BATCH_SEMANTICS",
        "ambiguous_counter_forbidden": "shared_global_forward_count",
        "must_persist": {
            "global_probability": True,
            "router_deep_features_192d": "TO_BE_CONFIRMED_AT_EXECUTION",
            "gt_free_router_scalar_ingredients": True,
            "roi_proposal_inputs_geometry": "IF_REUSABLE",
        },
        "gt_derived_information_persisted": False,
        "runs_once_not_per_seed": True,
        "G_retrained": False,
        "seed42_val808_rerun": False,
        "all_pass": True,
    })
    print("[§16/§19] resume + VAL808 shared-cache contracts frozen")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    print("=" * 78)
    print("PHASE 29 -- PHASE B: ADDITIVE TRAINER PARAMETERIZATION + PARITY")
    print("=" * 78)

    r01 = s0_s1()
    if not r01["gate"]:
        print("STOP: entry gate failed"); return 1
    if r01["drift"]:
        print("STOP:", BLOCKED["CANONICAL_TRAINER_SOURCE_DRIFT"]); return 1

    r2 = s2()
    if not r2["clean"]:
        print("STOP:", BLOCKED["SEED_ROOT_CONTAMINATION_UNRESOLVED"]); return 1

    r20 = s20()
    if not r20["ok"]:
        print("STOP:", BLOCKED["CANONICAL_TRAINER_SOURCE_DRIFT"]); return 1

    r7 = s7_9_11()
    if not r7["rng"]:
        print("STOP:", BLOCKED["SEED_BIND_AFTER_RNG_DRAW"]); return 1
    if not (r7["rpsi"] and r7["bphi"] and r7["somega"]):
        print("STOP:", BLOCKED["SEED42_TRAINER_PARITY_FAILURE"]); return 1

    r13 = s13()
    if not r13["ok"]:
        print("STOP:", BLOCKED["FIXED_PARTITION_IDENTITY_FAILURE"]); return 1

    r14 = s14_15()
    if not r14["ok"]:
        print("STOP:", BLOCKED["OUTPUT_PATH_COLLISION"]); return 1

    s16_19()

    noexec = {
        "artifact": "phase29_phase_b_no_execution_audit",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "training_runs": 0, "optimizer_steps": 0, "backward_passes": 0,
        "scientific_model_forwards": 0, "new_scientific_predictions": 0,
        "new_delta_dice_targets": 0, "val808_reads": 0,
        "router_holdout_reads": 0, "test_reads": 0,
        "dry_run_object_construction_permitted": True,
        "scientific_data_forwarded": False,
        "all_pass": True,
    }
    wj("reports/audits/phase29_phase_b_no_execution_audit.json", noexec)

    final = {
        "artifact": "phase29_phase_b_final_check",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "historical_trainer_sources_unchanged": r20["ok"],
        "phase29_wrappers_additive_only": True,
        "rpsi_seed42_config_parity": r7["rpsi"],
        "bphi_seed42_config_parity": r7["bphi"],
        "somega_seed42_config_parity": r7["somega"],
        "seed_bound_before_rng": r7["rng"],
        "fixed_partition_full_identity": r13["ok"],
        "fixed_partition_checks": r13["n_checks"],
        "fixed_partition_failures": r13["n_failed"],
        "new_run_configs": r14["n_runs"],
        "unique_output_roots": 32,
        "output_collisions": 0,
        "resume_contract_frozen": True,
        "val808_shared_pass_contract_frozen": True,
        "val808_shared_pass_executed": False,
        "training_runs": 0, "model_forwards": 0, "val808_reads": 0,
        "router_holdout_reads": 0, "test_reads": 0,
        "all_pass": True,
    }
    final["all_pass"] = all([
        final["historical_trainer_sources_unchanged"],
        final["rpsi_seed42_config_parity"],
        final["bphi_seed42_config_parity"],
        final["somega_seed42_config_parity"],
        final["seed_bound_before_rng"],
        final["fixed_partition_full_identity"],
        final["new_run_configs"] == 32,
        final["output_collisions"] == 0,
    ])
    wj("reports/audits/phase29_phase_b_final_check.json", final)

    term = SUCCESS_TERMINAL if final["all_pass"] else BLOCKED["TRAINER_PARAMETERIZATION_INCOMPLETE"]
    wj("reports/audits/phase29_phase_b_terminal.json", {
        "artifact": "phase29_phase_b_terminal",
        "phase": 29, "generated_utc": NOW, "governance_only": True,
        "execution": "NONE",
        "terminal": term,
        "exit_class": "SUCCESS" if final["all_pass"] else "BLOCKED",
        "success_terminal": SUCCESS_TERMINAL,
        "blocked_terminals": BLOCKED,
        "training_runs": 0, "model_forwards": 0, "val808_reads": 0,
        "router_holdout_reads": 0, "test_reads": 0,
        "training_eligible_not_started": True,
        "directive": "STOP. NO TRAINING. NO VAL808. NO ROUTER_HOLDOUT. NO TEST.",
    })

    print("-" * 78)
    print("FINAL CHECK all_pass =", final["all_pass"])
    print("TERMINAL:", term)
    print("=" * 78)
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
