"""Phase 25A — CROSS-FIT STRUCTURE + INNER FIT/EARLY-STOP SPLITS.

Frozen structure (Phase-24 v1.1 ``crossfit`` block, Phase-25A sections 12-13):

    * 3 outer folds (fold0, fold1, fold2) over ROUTER_DEVELOPMENT
    * deterministic, group-safe, domain-stratified, seed 42
    * OUTER_TARGET_k is NEVER used for gradient updates, checkpoint selection,
      early stopping or architecture selection
    * inside the two permitted training folds: a nested group-safe,
      domain-stratified 90% FIT / 10% EARLY_STOP split
    * no outer-target rows, no ROUTER_HOLDOUT, no existing VAL, no TEST

Writes:
    reports/audits/phase25a_crossfit_protocol.json
    reports/tables/phase25a_crossfit_fold_manifest_summary.csv
    data_cache/phase25a_global_cache/folds/fold{k}_{outer_target,fit,early_stop}.csv

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_crossfit.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FOLD_DIR = ROOT / "data_cache" / "phase25a_global_cache" / "folds"
UTC = datetime.now(timezone.utc).isoformat()

SEED = 42
N_OUTER = 3
FIT_FRACTION = 0.9
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
CACHE = ROOT / "data_cache" / "phase25a_global_cache"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stable_key(seed: int, group_key: str) -> str:
    return hashlib.sha256(f"{seed}::{group_key}".encode()).hexdigest()


def balanced_group_assignment(groups: list[tuple[str, int, str]], n_buckets: int,
                              seed: int, salt: str) -> dict[str, int]:
    """Deterministically assign whole groups to ``n_buckets`` balanced buckets.

    ``groups`` is a list of ``(group_key, n_samples, domain)``. Groups are ordered
    by ``sha256(f"{seed}::{salt}::{group_key}")`` and each group is placed into the
    currently smallest bucket (ties broken by bucket index). This is group-safe,
    deterministic and balances the realised sample counts.
    """
    ordered = sorted(groups, key=lambda g: stable_key(seed, f"{salt}::{g[0]}"))
    bucket_sizes = [0] * n_buckets
    assignment: dict[str, int] = {}
    for group_key, n_samples, _domain in ordered:
        target = min(range(n_buckets), key=lambda b: (bucket_sizes[b], b))
        assignment[group_key] = target
        bucket_sizes[target] += n_samples
    return assignment


def main() -> int:
    sm = pd.read_csv(SPLIT_MANIFEST)
    dev = sm[sm["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    assert len(dev) == 4957, len(dev)

    # domain-stratified outer fold assignment
    fold_of_group: dict[str, int] = {}
    for domain in sorted(dev["dataset"].unique()):
        sub = dev[dev["dataset"] == domain]
        groups = [(str(g), int(len(rows)), domain)
                  for g, rows in sub.groupby("group_key", sort=True)]
        fold_of_group.update(balanced_group_assignment(groups, N_OUTER, SEED, "outer"))
    dev["outer_fold"] = dev["group_key"].map(fold_of_group).astype(int)

    FOLD_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    fold_manifest_shas: dict[str, str] = {}
    fit_shas: dict[str, str] = {}
    es_shas: dict[str, str] = {}

    for k in range(N_OUTER):
        outer_target = dev[dev["outer_fold"] == k].copy()
        train_portion = dev[dev["outer_fold"] != k].copy()

        # nested 90/10 FIT / EARLY_STOP inside the training portion only
        inner_of_group: dict[str, int] = {}
        for domain in sorted(train_portion["dataset"].unique()):
            sub = train_portion[train_portion["dataset"] == domain]
            groups = [(str(g), int(len(rows)), domain)
                      for g, rows in sub.groupby("group_key", sort=True)]
            ordered = sorted(groups, key=lambda g: stable_key(SEED, f"inner90::{k}::{g[0]}"))
            target_es = round((1.0 - FIT_FRACTION) * sum(g[1] for g in groups))
            bucket: dict[str, int] = {}
            es_size = 0
            for group_key, n_samples, _d in ordered:
                if es_size < target_es:
                    bucket[group_key] = 1
                    es_size += n_samples
                else:
                    bucket[group_key] = 0
            inner_of_group.update(bucket)
        train_portion["inner_bucket"] = train_portion["group_key"].map(inner_of_group).astype(int)
        fit = train_portion[train_portion["inner_bucket"] == 0].copy()
        early_stop = train_portion[train_portion["inner_bucket"] == 1].copy()

        # ---- integrity checks ------------------------------------------- #
        assert set(fit["group_key"]) & set(early_stop["group_key"]) == set(), "FIT/ES group overlap"
        assert set(fit["group_key"]) & set(outer_target["group_key"]) == set(), "FIT/outer overlap"
        assert set(early_stop["group_key"]) & set(outer_target["group_key"]) == set(), \
            "ES/outer overlap"
        assert len(fit) + len(early_stop) + len(outer_target) == 4957, "population accounting"

        for name, frame in (("outer_target", outer_target), ("fit", fit),
                            ("early_stop", early_stop)):
            p = FOLD_DIR / f"fold{k}_{name}.csv"
            frame[["sample_id", "dataset", "task_id", "group_key", "outer_fold"]
                  ].to_csv(p, index=False)
            if name == "outer_target":
                fold_manifest_shas[f"fold{k}_outer_target"] = sha(p)
            elif name == "fit":
                fit_shas[f"fold{k}_fit"] = sha(p)
            else:
                es_shas[f"fold{k}_early_stop"] = sha(p)

        summary_rows.append({
            "fold": f"fold{k}",
            "outer_target_n": len(outer_target),
            "training_portion_n": len(train_portion),
            "fit_n": len(fit),
            "early_stop_n": len(early_stop),
            "early_stop_fraction": round(len(early_stop) / len(train_portion), 6),
            "fit_domains": json.dumps(fit["dataset"].value_counts().to_dict(), sort_keys=True),
            "early_stop_domains": json.dumps(early_stop["dataset"].value_counts().to_dict(),
                                             sort_keys=True),
            "outer_target_domains": json.dumps(
                outer_target["dataset"].value_counts().to_dict(), sort_keys=True),
            "group_overlap_fit_es": 0,
            "group_overlap_train_outer": 0,
        })

    pd.DataFrame(summary_rows).to_csv(TAB / "phase25a_crossfit_fold_manifest_summary.csv",
                                      index=False)

    protocol = {
        "artifact": "phase25a_crossfit_protocol",
        "phase": "25A",
        "purpose": "freeze the 3-fold cross-fit structure and the nested FIT/EARLY_STOP split so "
                   "no outer-target information can reach gradient updates, checkpoint selection, "
                   "early stopping or architecture selection",
        "seed": SEED,
        "outer_folds": N_OUTER,
        "within": "ROUTER_DEVELOPMENT",
        "assignment": "deterministic, group-safe, domain-stratified; per domain, whole groups are "
                      "ordered by sha256('42::<salt>::<group_key>') and placed into the currently "
                      "smallest bucket (ties by bucket index)",
        "group_key": "the frozen composite group key from phase24_router_split_manifest.csv",
        "inner_fit_fraction": FIT_FRACTION,
        "inner_early_stop_fraction": round(1.0 - FIT_FRACTION, 2),
        "inner_split_rules": ["group-safe", "domain-stratified", "seed 42"],
        "outer_target_role": "UNTOUCHED in Phase 25A; never used for training, checkpoint "
                             "selection, early stopping or architecture selection; its paired-gain "
                             "labels belong to Phase 25C",
        "oof_target_fold_never_used_for_checkpoint_selection": True,
        "deltadice_computed_in_phase25a": False,
        "folds": summary_rows,
        "fold_manifest_sha256": fold_manifest_shas,
        "fit_manifest_sha256": fit_shas,
        "early_stop_manifest_sha256": es_shas,
        "global_empty_samples_excluded_from_refiner_training": True,
        "global_empty_samples_retained_in_population_accounting": True,
        "router_holdout_used": False,
        "val_used": False,
        "test_reads": 0,
        "verdict": "PHASE25A_CROSSFIT_PROTOCOL_FROZEN",
        "generated_utc": UTC,
    }
    (AUD / "phase25a_crossfit_protocol.json").write_text(
        json.dumps(protocol, indent=1) + "\n", encoding="utf-8")

    print("=" * 78)
    print("PHASE 25A — CROSS-FIT STRUCTURE")
    print("=" * 78)
    for r in summary_rows:
        print(f"  {r['fold']}: outer_target={r['outer_target_n']:5d}  "
              f"fit={r['fit_n']:5d}  early_stop={r['early_stop_n']:5d}  "
              f"es_frac={r['early_stop_fraction']:.4f}")
    print(f"  total outer_target = {sum(r['outer_target_n'] for r in summary_rows)}")
    print(f"wrote {AUD / 'phase25a_crossfit_protocol.json'}")
    print(f"wrote {TAB / 'phase25a_crossfit_fold_manifest_summary.csv'}")
    print("PHASE25A_CROSSFIT_PROTOCOL_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
