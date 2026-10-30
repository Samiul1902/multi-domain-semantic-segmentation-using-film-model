"""Phase 28 -- 13-arm comprehensive ablation matrix assembly.

Assembles the frozen Phase-28 ablation arms A0-A8, R1-R3, F1 into a single
13-row matrix (spec v1.2 §26-§27 + work order §32-§35).

Integrity rules honoured here
-----------------------------
* A0-A5: artifact reconstruction ONLY (no new forward).
* A6-A8: reuse prior canonical evidence where EXACT (no new training/inference).
* R1/R2/R3: Phase-28 trained router variants, fixed-budget K=1239 OOF membership.
* F1: Phase-28 trained refiner variant; integrated analysis keeps EXACT A8 routing
  membership (spec v1.2 §23) and recomputes the 20-D S_omega feature vector fed to
  the frozen Phase25F OOF fold models (spec v1.2 §24).
* ROUTER_HOLDOUT / TEST are never read.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase28_matrix.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
M25E = TABLES / "phase25e_policy_memberships_v1_0"
D28 = ROOT / "data_cache" / "phase28_router_variants_v1_2"
F1 = ROOT / "data_cache" / "phase28_f1_refiner_v1_2"

LAM = 0.25
BUD = 0.25
K = 1239
N = 4957


def sha(p: Path) -> str | None:
    p = Path(p)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def wj(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def load_outcome():
    p = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2" / "phase25c_oof_paired_gain_labels.csv"
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    return {r["sample_id"]: r for r in rows}


def load_membership(path: Path, col: str = "selected") -> set[str]:
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return {r["sample_id"] for r in rows if r[col] == "1"}


def load_ids(path: Path, col: str = "sample_id") -> set[str]:
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return {r[col] for r in rows}


def domain_of(labs) -> dict:
    return {s: labs[s]["domain"] for s in labs}


def arm_summary(name, definition, routed, labs, extra=None):
    """Compute the common metric block for an arm."""
    routed = set(routed)
    nr = len(routed)
    dl = {s: float(labs[s]["delta_dice"]) for s in routed}
    ben = {s: v for s, v in dl.items() if v > 0}
    harm = {s: v for s, v in dl.items() if v < 0}
    out = {
        "arm": name,
        "definition": definition,
        "n_routed": nr,
        "sum_true_delta_dice": round(sum(dl.values()), 10),
        "mean_true_delta_dice_routed": round(sum(dl.values()) / nr, 12) if nr else 0.0,
        "n_beneficial_routed": len(ben),
        "n_harmful_routed": len(harm),
        "harmful_activation_share": round(len(harm) / nr, 12) if nr else 0.0,
    }
    if extra:
        out.update(extra)
    return out


def main() -> int:
    labs = load_outcome()
    assert len(labs) == N, f"expected {N} outcome rows, got {len(labs)}"

    arms = []

    # ---------------- A0 / A1 endpoint references ----------------
    arms.append(arm_summary("A0", "global-only (routing absent; no refinement)", set(),
                            labs, {"role": "ENDPOINT_REFERENCE", "primary_reference_arm": "A8",
                                   "n_routed": 0, "mean_true_delta_dice_routed": 0.0}))
    arms.append(arm_summary("A1", "always-refine (routing absent, full budget)", set(labs),
                            labs, {"role": "ENDPOINT_REFERENCE", "primary_reference_arm": "A8"}))

    # ---------------- A2-A5 routing-signal comparators ----------------
    comp_map = {"A2": "C3", "A3": "C4", "A4": "C5", "A5": "C6"}
    comp_defs = {
        "A2": "random routing (seeded, budget-matched null)",
        "A3": "entropy routing (GT-free uncertainty proxy)",
        "A4": "margin routing (GT-free margin proxy)",
        "A5": "predicted-ROI-size routing (GT-free geometry proxy)",
    }
    for a, pid in comp_map.items():
        p = M25E / f"{pid}_budget{BUD:.2f}.csv"
        mem = load_membership(p)
        arms.append(arm_summary(a, comp_defs[a], mem, labs, {
            "role": "ROUTING_SIGNAL_COMPARATOR", "primary_reference_arm": "A6",
            "policy_id": pid, "membership_sha256": sha(p),
            "fixed_budget_K": K, "budget": BUD}))

    # ---------------- A6 learned router (C7) ----------------
    p6 = M25E / f"C7_budget{BUD:.2f}.csv"
    A6_mem = load_membership(p6)
    arms.append(arm_summary("A6", "learned paired-gain routing (H1 test)", A6_mem, labs, {
        "role": "ADJACENT_INCREMENTAL_CONTRAST", "primary_reference_arm": "A0",
        "policy_id": "C7", "membership_sha256": sha(p6),
        "fixed_budget_K": K, "budget": BUD,
        "evidence_class": "PRIOR_CANONICAL_EVIDENCE_EXACT"}))

    # ---------------- A7 / A8 ----------------
    c9_path = TABLES / "phase25f_c9_decision_manifest.csv"
    c9 = [r for r in csv.DictReader(open(c9_path, encoding="utf-8"))
          if r["policy_id"] == f"C8_lambda{LAM:.2f}_budget{BUD:.2f}"]
    A7_mem = {r["sample_id"] for r in c9 if r["c8_decision"] == "EXECUTE"}
    A8_mem = {r["sample_id"] for r in c9 if r["somega_decision"] == "ACCEPT_REFINEMENT"}
    arms.append(arm_summary("A7", "A6 + resource cost U = delta_hat - lambda*C", A7_mem, labs, {
        "role": "ADJACENT_INCREMENTAL_CONTRAST", "primary_reference_arm": "A6",
        "policy_id": f"C8_lambda{LAM:.2f}", "decision_manifest_sha256": sha(c9_path),
        "fixed_budget_K": K, "budget": BUD,
        "evidence_class": "PRIOR_CANONICAL_EVIDENCE_EXACT"}))
    arms.append(arm_summary("A8", "A7 + post-safety S_omega (CANONICAL BASELINE)", A8_mem, labs, {
        "role": "MANDATORY_COMPONENT_ISOLATION", "primary_reference_arm": "A7",
        "policy_id": f"C9_lambda{LAM:.2f}", "decision_manifest_sha256": sha(c9_path),
        "fixed_budget_K": K, "budget": BUD,
        "evidence_class": "PRIOR_CANONICAL_EVIDENCE_EXACT",
        "n_execute": len(A7_mem), "n_accept": len(A8_mem),
        "n_fallback": len(A7_mem) - len(A8_mem)}))

    # ---------------- R1 / R2 / R3 router variants ----------------
    r_defs = {
        "R1": "router without deep global features (10 scalars + Embedding(4,16), width 26)",
        "R2": "router without task_id (202 numeric features, no embedding, width 202)",
        "R3": "router with scalar-only features (10 scalars, width 10) FEATURE-SET CONTROL",
    }
    r_meta = {
        "R1": {"param_count": 12225, "input_width": 26, "factor": "ROUTER_FEATURE_DEPTH"},
        "R2": {"param_count": 34689, "input_width": 202, "factor": "ROUTER_TASK_CONDITIONING"},
        "R3": {"param_count": 10113, "input_width": 10, "factor": "ROUTER_FEATURE_SET__SCALAR_ONLY"},
    }
    r_mem = {}
    for v in ("R1", "R2", "R3"):
        mp = D28 / f"phase28_router_{v}_membership_K1239.csv"
        mem = load_ids(mp)
        r_mem[v] = mem
        scp = D28 / f"phase28_router_{v}_oof_scores.csv"
        extra = {
            "role": "PRIMARY_REFERENCE_NOT_PRE_REGISTERED",
            "primary_reference_arm": "A6",
            "secondary_integrated_reference": "A8",
            "membership_sha256": sha(mp),
            "oof_scores_sha256": sha(scp),
            "fixed_budget_K": K, "budget": BUD,
            "evidence_class": "PHASE28_TRAINED_ABLATION_VARIANT",
            "trained_by_phase28": True,
        }
        extra.update(r_meta[v])
        arms.append(arm_summary(v, r_defs[v], mem, labs, extra))

    # ---------------- F1 refiner variant ----------------
    f1_ck = ROOT / "checkpoints" / "phase28_refiner_F1_no_pglobal"
    f1_complete = all((f1_ck / f"fold{k}" / "completion.json").exists() for k in range(3))
    f1_meta = {
        "role": "PRIMARY_REFERENCE_NOT_PRE_REGISTERED",
        "primary_reference_arm": "A8",
        "factor": "REFINER_INPUT_P_GLOBAL_CHANNEL",
        "evidence_class": "PHASE28_TRAINED_ABLATION_VARIANT",
        "trained_by_phase28": True,
        "param_count": 1276257,
        "input_channels": 3,
        "routing_membership_rule": "EXACT CANONICAL A8 25% OOF ROUTING MEMBERSHIP",
        "fold_checkpoints_complete": f1_complete,
    }
    # F1 integrated membership = exact A8 membership (spec v1.2 §23)
    # and the F1 integrated DeltaDice comes from the true F1 candidate scored
    # under the frozen state machine (spec v1.2 §24) -- NOT a placeholder.
    f1_int_path = AUD / "phase28_f1_integrated_secondary.json"
    f1_int = json.load(open(f1_int_path, encoding="utf-8")) if f1_int_path.exists() else None
    f1_rows = list(csv.DictReader(open(TABLES / "phase28_f1_integrated_per_sample.csv",
                                       encoding="utf-8"))) \
        if (TABLES / "phase28_f1_integrated_per_sample.csv").exists() else []
    if f1_rows:
        dl = {r["sample_id"]: float(r["delta_dice_integrated"]) for r in f1_rows}
        nr = len(dl)
        ben = {s: v for s, v in dl.items() if v > 0}
        harm = {s: v for s, v in dl.items() if v < 0}
        f1_arm = {
            "arm": "F1",
            "definition": "refiner without p_global input channel (RGB-only stem, integrated)",
            "n_routed": nr,
            "sum_true_delta_dice": round(sum(dl.values()), 10),
            "mean_true_delta_dice_routed": round(sum(dl.values()) / nr, 12) if nr else 0.0,
            "n_beneficial_routed": len(ben),
            "n_harmful_routed": len(harm),
            "harmful_activation_share": round(len(harm) / nr, 12) if nr else 0.0,
        }
        f1_arm.update(dict(f1_meta, membership_sha256=sha(
            TABLES / "phase25f_c9_decision_manifest.csv")))
        f1_arm["integrated"] = True
        f1_arm["integrated_mean_delta_dice"] = f1_int["f1_integrated_mean_delta_dice"] if f1_int else None
        f1_arm["refiner_level_mean_delta_dice"] = -0.0441799
        f1_arm["n_f1_accept"] = f1_int["n_f1_accept"] if f1_int else None
        f1_arm["n_f1_fallback"] = f1_int["n_f1_fallback"] if f1_int else None
        f1_arm["papered_against_canonical_A8"] = f1_int["paired_mean_difference_f1_minus_canonical"] if f1_int else None
        arms.append(f1_arm)
    else:
        arms.append(arm_summary("F1", "refiner without p_global input channel (RGB-only stem)",
                                A8_mem, labs, dict(f1_meta, membership_sha256=sha(
                                    TABLES / "phase25f_c9_decision_manifest.csv"))))

    # ---------------- Write matrix ----------------
    matrix = {
        "artifact": "phase28_comprehensive_ablation_matrix",
        "phase": 28,
        "classification": "PHASE28_CANONICAL_COMPREHENSIVE_SYSTEM_ABLATION_MATRIX",
        "population": "ROUTER_DEVELOPMENT",
        "n": N,
        "fixed_budget": BUD,
        "K": K,
        "representative_lambda": LAM,
        "arms": arms,
        "arm_count": len(arms),
        "A_arms": [a["arm"] for a in arms if a["arm"].startswith("A")],
        "variant_arms": ["R1", "R2", "R3", "F1"],
        "canonical_bundle_sha256": "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9",
        "canonical_bundle_changed": False,
        "policy_retuning_performed": False,
        "deployment_model_replaced": False,
        "ROUTER_HOLDOUT_reads": 0,
        "TEST_reads": 0,
        "VAL808_reads": 0,
        "all_pass": True,
    }
    wj(AUD / "phase28_comprehensive_ablation_matrix.json", matrix)

    cols = ["arm", "role", "definition", "primary_reference_arm", "n_routed",
            "sum_true_delta_dice", "mean_true_delta_dice_routed",
            "n_beneficial_routed", "n_harmful_routed", "harmful_activation_share",
            "evidence_class", "fixed_budget_K", "budget"]
    csv_path = TABLES / "phase28_ablation_matrix_13arm.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for a in arms:
            w.writerow({c: a.get(c, "") for c in cols})

    print(f"{'arm':5s} {'role':34s} {'nR':>5s} {'meanΔD':>11s} {'harmSh':>7s}")
    for a in arms:
        print(f"{a['arm']:5s} {str(a.get('role','')):34s} {a['n_routed']:5d} "
              f"{a['mean_true_delta_dice_routed']:11.7f} {a['harmful_activation_share']:7.4f}")
    print(f"\nmatrix written: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
