"""POST-PHASE-13 REVISION R0-B — R1 policy membership / tie-break freeze.

Label-blind membership derivation. NO model inference, NO training, NO proposal regeneration.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
FREEZE_UTC = "2026-09-22T06:09:00Z"
TOL = 1e-12


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def membership_hash(df: pd.DataFrame) -> str:
    """Deterministic SHA-256 over (sample_id, proposal_rank, accepted) ordered by
    sample_id lexical ascending then proposal_rank ascending."""
    d = df.sort_values(["sample_id", "proposal_rank"], kind="mergesort")
    payload = "".join(f"{r.sample_id}|{int(r.proposal_rank)}|{1 if r.accepted else 0}\n"
                      for r in d.itertuples())
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> dict:
    fam = pd.read_csv(TABLES / "post_phase13_regional_revision_r1_candidate_family.csv")
    prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    casep = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")

    # ---- label-blind input: ONLY sample_id / proposal_rank / proposal_score ----
    base = prop[["sample_id", "proposal_rank", "proposal_score"]].copy()
    assert len(base) == 494
    assert not base[["sample_id", "proposal_rank", "proposal_score"]].isna().any().any()
    assert base.duplicated(["sample_id", "proposal_rank"]).sum() == 0

    memberships, summaries, hashes = [], [], {}
    for r in fam.itertuples():
        floor = float(r.score_acceptance_floor)
        cap = int(r.max_accepted_proposals)
        m = base.copy()
        m["config_id"] = r.config_id
        m["score_acceptance_floor"] = floor
        m["score_passes_floor"] = (m["proposal_score"] >= floor)
        m["max_accepted_proposals"] = cap
        # deterministic order: frozen proposal_rank ASCENDING within each case
        m = m.sort_values(["sample_id", "proposal_rank"], kind="mergesort").reset_index(drop=True)
        m["selected_by_rank_cap"] = False
        m["accepted_order_within_case"] = pd.NA
        for sid, idx in m.groupby("sample_id", sort=True).groups.items():
            cand = m.loc[idx][m.loc[idx, "score_passes_floor"]]
            take = cand.sort_values("proposal_rank", kind="mergesort").head(cap)
            if len(take):
                m.loc[take.index, "selected_by_rank_cap"] = True
                m.loc[take.index, "accepted_order_within_case"] = list(range(1, len(take) + 1))
        m["accepted"] = m["score_passes_floor"] & m["selected_by_rank_cap"]
        memberships.append(m)

        per_case = m.groupby("sample_id")["accepted"].sum()
        per_case = per_case.reindex(sorted(base["sample_id"].unique()), fill_value=0)
        vc = per_case.value_counts().to_dict()
        h = membership_hash(m)
        hashes[r.config_id] = h
        summaries.append({
            "config_id": r.config_id, "role": r.role, "score_floor": floor,
            "max_accepted_proposals": cap,
            "accepted_proposals_total": int(m["accepted"].sum()),
            "rejected_proposals_total": int((~m["accepted"]).sum()),
            "cases_with_0_accepted": int(vc.get(0, 0)),
            "cases_with_1_accepted": int(vc.get(1, 0)),
            "cases_with_2_accepted": int(vc.get(2, 0)),
            "cases_with_3_accepted": int(vc.get(3, 0)),
            "cases_with_4_accepted": int(vc.get(4, 0)),
            "cases_with_5_accepted": int(vc.get(5, 0)),
            "mean_accepted_per_case": float(per_case.mean()),
            "median_accepted_per_case": float(per_case.median()),
            "accepted_membership_sha256": h,
        })

    mem = pd.concat(memberships, ignore_index=True)
    cols = ["config_id", "sample_id", "proposal_rank", "proposal_score",
            "score_acceptance_floor", "score_passes_floor", "max_accepted_proposals",
            "selected_by_rank_cap", "accepted", "accepted_order_within_case"]
    mem = mem[cols]
    assert len(mem) == 7 * 494, len(mem)
    mem.to_csv(TABLES / "post_phase13_regional_revision_r1_frozen_membership.csv", index=False)

    summ = pd.DataFrame(summaries)
    assert len(summ) == 7, len(summ)
    summ.to_csv(TABLES / "post_phase13_regional_revision_r1_membership_summary.csv", index=False)

    # ---------------- §8 control identity gate ----------------
    c0 = mem[mem["config_id"] == "R1-C0"]
    p1c_counts = prop.groupby("sample_id").size()
    c0_counts = c0.groupby("sample_id")["accepted"].sum().reindex(p1c_counts.index)
    control_ok = (int(c0["accepted"].sum()) == 494) and bool((c0_counts == p1c_counts).all())

    # ---------------- §9 candidate relationships ----------------
    sets = {c: set(map(tuple, mem[(mem["config_id"] == c) & mem["accepted"]]
                       [["sample_id", "proposal_rank"]].to_numpy()))
            for c in fam["config_id"]}
    floors = dict(zip(fam["config_id"], fam["score_acceptance_floor"].astype(float)))
    caps = dict(zip(fam["config_id"], fam["max_accepted_proposals"].astype(int)))

    checks = []
    # (a) same cap, floor monotonicity
    for cap_val in sorted(set(caps.values())):
        ids = [c for c in fam["config_id"] if caps[c] == cap_val]
        ids = sorted(ids, key=lambda c: floors[c])
        for lo, hi in zip(ids, ids[1:]):
            ok = sets[hi] <= sets[lo]
            checks.append({"check": "floor_monotonicity_same_cap",
                           "lower_floor_config": lo, "higher_floor_config": hi,
                           "max_accepted_proposals": cap_val,
                           "higher_floor_subset_of_lower_floor": bool(ok),
                           "added_by_raising_floor": len(sets[hi] - sets[lo]),
                           "pass": bool(ok)})
    # (b) same floor, cap subset
    for fl in sorted(set(floors.values())):
        ids = [c for c in fam["config_id"] if floors[c] == fl]
        ids = sorted(ids, key=lambda c: caps[c])
        for small, big in zip(ids, ids[1:]):
            ok = sets[small] <= sets[big]
            checks.append({"check": "cap_subset_same_floor",
                           "smaller_cap_config": small, "larger_cap_config": big,
                           "score_floor": fl,
                           "smaller_cap_subset_of_larger_cap": bool(ok),
                           "pass": bool(ok)})
    rel_ok = all(c["pass"] for c in checks)

    # ---------------- §10 tie audit ----------------
    mx = float(prop["proposal_score"].max())
    tied = prop["proposal_score"] >= mx - TOL
    r1 = prop[prop["proposal_rank"] == 1]
    r1_tied = int((r1["proposal_score"] >= mx - TOL).sum())
    # proposals strictly between the stored 0.125065 floor and the exact max
    between = prop[(prop["proposal_score"] > 0.125065 + TOL) & (prop["proposal_score"] < mx - TOL)]
    tie = {
        "proposal_count": int(len(prop)),
        "marginal_max_score_exact": repr(mx),
        "count_exactly_at_max": int(tied.sum()),
        "fraction_exactly_at_max": float(tied.mean()),
        "rank1_saturated_count": r1_tied,
        "rank1_count": int(len(r1)),
        "rank2_saturated_count": int(((prop["proposal_rank"] == 2) &
                                      (prop["proposal_score"] >= mx - TOL)).sum()),
        "proposals_strictly_between_stored_floor_and_exact_max": int(len(between)),
        "stored_floor_max_config": 0.125065,
        "passes_floor_max_config_count": int((prop["proposal_score"] >= 0.125065).sum()),
        "statement": (
            "Because many proposals are tied at the marginal maximum, proposal_rank is used ONLY as "
            "the already-frozen deterministic ordering. R1 must NOT claim that rank 1 is necessarily "
            "more confident than rank 2 within an exact score tie."),
    }

    # ---------------- §11 persisted-language check ----------------
    needles = ["not a representation failure", "not representation failure"]
    hits = []
    for p in [AUDITS / "post_phase13_regional_revision_r0_failure_decomposition.json",
              AUDITS / "post_phase13_regional_revision_r0_failure_decomposition.md",
              AUDITS / "post_phase13_regional_revision_r0_protocol_frozen.json",
              AUDITS / "post_phase13_regional_revision_r0_protocol_frozen.md",
              ROOT / "docs" / "TASKS.md", ROOT / "docs" / "MEMORY.md"]:
        t = p.read_text(encoding="utf-8", errors="ignore")
        for n in needles:
            if n in t:
                hits.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "needle": n})
    clarification_required = len(hits) > 0

    return {"fam": fam, "prop": prop, "mem": mem, "summ": summ, "hashes": hashes,
            "control_ok": control_ok, "checks": checks, "rel_ok": rel_ok,
            "tie": tie, "hits": hits, "clarification_required": clarification_required,
            "c0_counts": c0_counts, "p1c_counts": p1c_counts, "sets": sets,
            "floors": floors, "caps": caps}


if __name__ == "__main__":
    r = main()
    print("=== membership summary ===")
    print(r["summ"][["config_id", "score_floor", "max_accepted_proposals",
                     "accepted_proposals_total", "cases_with_0_accepted",
                     "cases_with_1_accepted", "mean_accepted_per_case"]].to_string(index=False))
    print("\ncontrol identity (494 + per-case match):", r["control_ok"])
    print("relationships all pass:", r["rel_ok"])
    for c in r["checks"]:
        print("  ", c)
    print("\ntie audit:", json.dumps(r["tie"], indent=2))
    print("\nclarification required:", r["clarification_required"], "hits:", len(r["hits"]))
