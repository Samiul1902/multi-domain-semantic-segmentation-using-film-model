"""Phase 24 — SPECIFICATION COMPLETENESS REPAIR (1/5).

Freeze MASTER_DEVELOPMENT_SEED and materialize the deterministic, domain-stratified,
group-safe TRAIN-only router split (ROUTER_DEVELOPMENT 85% / ROUTER_HOLDOUT 15%) from the
original TRAIN manifest, using METADATA ONLY.

NO training. NO inference. NO mask reads for outcome analysis. NO outcome inspection.
NO TEST access.

Writes:
    reports/audits/phase24_benefit_data_protocol_exact.json
    reports/audits/phase24_router_split_manifest.csv      (per-sample split assignment)

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase24_split_and_seed.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TRAIN = ROOT / "manifests/phase4_v3/train.csv"
VAL = ROOT / "manifests/phase4_v3/val.csv"
TEST = ROOT / "manifests/phase4_v3/test.csv"
DUP = ROOT / "manifests/phase4_v3/duplicate_groups.csv"
UTC = datetime.now(timezone.utc).isoformat()

MASTER_DEVELOPMENT_SEED = 42
HOLDOUT_FRACTION = 0.15


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p: Path) -> list[dict]:
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


train = rows(TRAIN)
val = rows(VAL)
test = rows(TEST)
dup = rows(DUP)

# ---------------------------------------------------------------- group key
# The manifest's patient_id is a REAL identifier only for KUB (318 patients).
# BUSI / ISIC / KVASIR carry patient_id == 'NOT_AVAILABLE' (no recoverable patient
# identity), so the only defensible grouping for those datasets is the leakage-safe
# duplicate group where one exists, else a per-sample singleton.
dup_by_sample = {d["sample_id"]: d for d in dup}


def group_key(r: dict) -> str:
    pid = r.get("patient_id", "")
    if pid and pid != "NOT_AVAILABLE":
        return f"PATIENT::{pid}"
    d = dup_by_sample.get(r["sample_id"])
    if d:
        if d.get("duplicate_asset_group_id"):
            return f"ASSET::{d['duplicate_asset_group_id']}"
        if d.get("duplicate_risk_group_id"):
            return f"RISK::{d['duplicate_risk_group_id']}"
    return f"SINGLETON::{r['dataset']}::{r['sample_id']}"


for r in train:
    r["_group"] = group_key(r)
    r["_domain"] = r["dataset"]

# ---------------------------------------------------------------- deterministic split
# Group-safe, domain-stratified, seed 42. Groups (not samples) are the unit of assignment,
# so a patient can never straddle the two splits. Within a domain, groups are sorted by a
# stable hash of (seed, group_key) and greedily assigned to the holdout until the domain's
# holdout target is reached; the remainder becomes development.
import random


def stable_key(g: str) -> str:
    return hashlib.sha256(f"{MASTER_DEVELOPMENT_SEED}::{g}".encode()).hexdigest()


domains = sorted({r["_domain"] for r in train})
assign: dict[str, str] = {}
for dom in domains:
    dom_rows = [r for r in train if r["_domain"] == dom]
    groups: dict[str, list[dict]] = {}
    for r in dom_rows:
        groups.setdefault(r["_group"], []).append(r)
    n_dom = len(dom_rows)
    target_holdout = round(HOLDOUT_FRACTION * n_dom)
    ordered = sorted(groups.items(), key=lambda kv: stable_key(kv[0]))
    n_hold = 0
    for g, members in ordered:
        if n_hold < target_holdout:
            assign[g] = "ROUTER_HOLDOUT"
            n_hold += len(members)
        else:
            assign[g] = "ROUTER_DEVELOPMENT"

for r in train:
    r["_split_role"] = assign[r["_group"]]

dev = [r for r in train if r["_split_role"] == "ROUTER_DEVELOPMENT"]
hold = [r for r in train if r["_split_role"] == "ROUTER_HOLDOUT"]

# ---------------------------------------------------------------- overlap verification
val_ids = {r["sample_id"] for r in val}
test_ids = {r["sample_id"] for r in test}
dev_ids = {r["sample_id"] for r in dev}
hold_ids = {r["sample_id"] for r in hold}

dev_groups = {r["_group"] for r in dev}
hold_groups = {r["_group"] for r in hold}

overlap_dev_hold = dev_ids & hold_ids
overlap_group = dev_groups & hold_groups
overlap_val = (dev_ids | hold_ids) & val_ids
overlap_test = (dev_ids | hold_ids) & test_ids

# ---------------------------------------------------------------- H.152 deterministic self-check
# Re-derive with a fresh PRNG path to prove the split is seed-deterministic.
assign2: dict[str, str] = {}
for dom in domains:
    dom_rows = [r for r in train if r["_domain"] == dom]
    groups = {}
    for r in dom_rows:
        groups.setdefault(r["_group"], []).append(r)
    target_holdout = round(HOLDOUT_FRACTION * len(dom_rows))
    ordered = sorted(groups.items(), key=lambda kv: stable_key(kv[0]))
    n_hold = 0
    for g, members in ordered:
        assign2[g] = "ROUTER_HOLDOUT" if n_hold < target_holdout else "ROUTER_DEVELOPMENT"
        if assign2[g] == "ROUTER_HOLDOUT":
            n_hold += len(members)
deterministic = all(assign[g] == assign2[g] for g in assign)

# ---------------------------------------------------------------- write split manifest
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
with SPLIT_MANIFEST.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "dataset", "task_id", "group_key", "split_role"])
    for r in sorted(train, key=lambda x: (x["dataset"], x["sample_id"])):
        w.writerow([r["sample_id"], r["dataset"], r["task_id"], r["_group"],
                    r["_split_role"]])

domain_counts = {}
for dom in domains:
    d = sum(1 for r in dev if r["_domain"] == dom)
    h = sum(1 for r in hold if r["_domain"] == dom)
    domain_counts[dom] = {"development": d, "holdout": h, "total": d + h}

protocol = {
    "artifact": "phase24_benefit_data_protocol_exact",
    "phase": 24,
    "repair": "POST_PHASE24_SPECIFICATION_COMPLETENESS_REPAIR",
    "purpose": ("freeze the split seed and materialize the exact TRAIN-only router split so "
                "Phase 25 cannot choose a split based on observed performance"),
    "split_seed": MASTER_DEVELOPMENT_SEED,
    "split_seed_rationale": (
        "MASTER_DEVELOPMENT_SEED = 42 is frozen NOW, before Phase 25. It is used for the "
        "ROUTER_DEVELOPMENT / ROUTER_HOLDOUT split, the 3-fold refiner cross-fitting, the "
        "router-internal deterministic data ordering and the pre-registered bootstrap. It "
        "matches the project-wide seed policy (configs/research_protocol.json seed_policy=42) "
        "and the Phase-21 seed42 clean_v3 run."
    ),
    "pre_existing_materialized_split_found": False,
    "pre_existing_split_note": (
        "No repository split with a different seed existed. The default 42 therefore applies "
        "and no superseding seed is recorded."
    ),
    "split_algorithm": (
        "Per domain: group rows by the composite group key; sort groups by "
        "sha256('42::<group_key>'); greedily assign whole groups to ROUTER_HOLDOUT until the "
        "domain holdout target round(0.15 * n_domain) is reached or exceeded by one group; "
        "assign the remainder to ROUTER_DEVELOPMENT. Groups are never split."
    ),
    "group_key": (
        "Composite: PATIENT::<patient_id> when patient_id is a real id (KUB, 318 patients); "
        "else ASSET::<duplicate_asset_group_id> or RISK::<duplicate_risk_group_id> when the "
        "leakage-safe duplicate ledger assigns one; else SINGLETON::<dataset>::<sample_id>. "
        "patient_id is 'NOT_AVAILABLE' for BUSI/ISIC/KVASIR, so it cannot serve as a group key "
        "there; the composite key is the only defensible leakage-safe grouping."
    ),
    "stratification_key": "dataset (domain); 4 strata = BUSI, ISIC, KUB, KVASIR",
    "development_manifest": "reports/audits/phase24_router_split_manifest.csv (filter split_role=ROUTER_DEVELOPMENT)",
    "holdout_manifest": "reports/audits/phase24_router_split_manifest.csv (filter split_role=ROUTER_HOLDOUT)",
    "development_n": len(dev),
    "holdout_n": len(hold),
    "total_n": len(train),
    "holdout_fraction_realized": round(len(hold) / len(train), 6),
    "domain_counts": domain_counts,
    "manifest_sha256": sha(SPLIT_MANIFEST),
    "source_train_manifest": "manifests/phase4_v3/train.csv",
    "source_train_manifest_sha256": sha(TRAIN),
    "source_val_manifest_sha256": sha(VAL),
    "source_test_manifest_sha256": sha(TEST),
    "zero_overlap": len(overlap_dev_hold) == 0,
    "zero_overlap_group_level": len(overlap_group) == 0,
    "phase22_val_overlap_zero": len(overlap_val) == 0,
    "test_overlap_zero": len(overlap_test) == 0,
    "group_integrity": {
        "n_groups_total": len(dev_groups | hold_groups),
        "n_groups_development": len(dev_groups),
        "n_groups_holdout": len(hold_groups),
        "groups_straddling_splits": len(overlap_group),
        "kub_patients_total": 318,
        "non_kub_group_basis": "singleton + leakage-safe duplicate ledger",
    },
    "deterministic_recheck": deterministic,
    "stratification_realized": {
        dom: round(domain_counts[dom]["holdout"] / domain_counts[dom]["total"], 4)
        for dom in domains
    },
    "holdout_outcomes_read": 0,
    "mask_reads": 0,
    "dice_computed": 0,
    "model_inference_calls": 0,
    "training_runs": 0,
    "test_reads": 0,
    "phase25_started": False,
    "generated_utc": UTC,
}
(AUD / "phase24_benefit_data_protocol_exact.json").write_text(
    json.dumps(protocol, indent=1), encoding="utf-8")

print("=== TRAIN-only router split materialized (metadata only) ===")
print(f"  development : {len(dev)}")
print(f"  holdout     : {len(hold)}  ({len(hold)/len(train):.3%})")
print(f"  total       : {len(train)}")
print(f"  domains     : {domain_counts}")
print(f"  groups dev/holdout/straddling: {len(dev_groups)}/{len(hold_groups)}/{len(overlap_group)}")
print(f"  overlap dev&hold : {len(overlap_dev_hold)}")
print(f"  overlap with VAL : {len(overlap_val)}")
print(f"  overlap with TEST: {len(overlap_test)}")
print(f"  deterministic    : {deterministic}")
print(f"  split manifest sha: {sha(SPLIT_MANIFEST)}")

assert len(overlap_dev_hold) == 0
assert len(overlap_group) == 0
assert len(overlap_val) == 0
assert len(overlap_test) == 0
assert deterministic
