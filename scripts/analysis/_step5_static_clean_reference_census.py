import csv
import json
import os
from collections import Counter

ROOT = r"D:\Softfors\jup"

scores_p = os.path.join(ROOT, "reports", "tables", "phase27_val808_per_sample_scores.csv")
routing_p = os.path.join(ROOT, "data_cache", "phase29_seed42", "phase29_seed42_val808_decisions.csv")
manifest_p = os.path.join(ROOT, "manifests", "phase4_v3", "val.csv")

out = {}


def _num_ok(s):
    try:
        return float(s) == float(s)
    except Exception:
        return False


def census(name, path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames
        rows = list(rd)
    ids = [r.get("sample_id") for r in rows]
    c = Counter(ids)
    dup = sorted([k for k, v in c.items() if v > 1])
    return {"row_count": len(rows), "columns": cols, "sample_id_count": len(ids),
            "unique_sample_id_count": len(set(ids)), "duplicate_ids": dup,
            "ids": set(ids), "rows": rows}


sc = census("per_sample_scores", scores_p)
rt = census("routing_state", routing_p)
mf = census("val_manifest", manifest_p)

out["per_sample_scores"] = {
    "path": "reports/tables/phase27_val808_per_sample_scores.csv",
    "row_count": sc["row_count"],
    "columns": sc["columns"],
    "unique_sample_id_count": sc["unique_sample_id_count"],
    "duplicate_ids": sc["duplicate_ids"],
    "sample_id_set_size": len(sc["ids"]),
}
# domain distribution
dom = Counter(r.get("dataset") or r.get("domain") for r in sc["rows"])
out["per_sample_scores"]["dataset_counts"] = dict(dom)
# final_dice finite count
fd_finite = sum(1 for r in sc["rows"] if r.get("final_dice") not in (None, "", "nan", "NaN")
                and _num_ok(r.get("final_dice")))
out["per_sample_scores"]["final_dice_finite_count"] = fd_finite


# state_machine_branch + router_decision value counts
smb = Counter(r.get("state_machine_branch") for r in sc["rows"])
rd = Counter(r.get("router_decision") for r in sc["rows"])
out["per_sample_scores"]["state_machine_branch_counts"] = dict(smb)
out["per_sample_scores"]["router_decision_counts"] = dict(rd)

out["routing_state"] = {
    "path": "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv",
    "row_count": rt["row_count"],
    "columns": rt["columns"],
    "unique_sample_id_count": rt["unique_sample_id_count"],
    "duplicate_ids": rt["duplicate_ids"],
    "sample_id_set_size": len(rt["ids"]),
}
sel = Counter(r.get("selected") for r in rt["rows"])
out["routing_state"]["selected_value_counts"] = dict(sel)

out["val_manifest"] = {
    "path": "manifests/phase4_v3/val.csv",
    "row_count": mf["row_count"],
    "columns": mf["columns"],
    "unique_sample_id_count": mf["unique_sample_id_count"],
    "duplicate_ids": mf["duplicate_ids"],
    "sample_id_set_size": len(mf["ids"]),
}
mdom = Counter(r.get("dataset") or r.get("domain") for r in mf["rows"])
out["val_manifest"]["dataset_counts"] = dict(mdom)

# Set comparisons (sample-ID namespace)
S = sc["ids"]
R = rt["ids"]
M = mf["ids"]
out["set_comparison"] = {
    "scores_n": len(S), "routing_n": len(R), "manifest_n": len(M),
    "scores_vs_manifest": {
        "missing_from_clean_reference": sorted(M - S),
        "extra_in_clean_reference": sorted(S - M),
    },
    "routing_vs_manifest": {
        "missing_from_routing_reference": sorted(M - R),
        "extra_in_routing_reference": sorted(R - M),
    },
    "scores_vs_routing": {
        "only_in_scores": sorted(S - R),
        "only_in_routing": sorted(R - S),
    },
}

# Also: do the scores CSV and manifest agree on task_id / dataset per sample?
# And does the routing CSV carry the same task_id?
print(json.dumps(out, indent=1, default=str))
