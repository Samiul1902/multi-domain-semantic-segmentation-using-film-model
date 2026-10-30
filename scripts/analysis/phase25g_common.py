"""Phase25G common module - RA-MedFiLM-BARR integrated controlled development evaluation.

ARTIFACT-LEVEL EVALUATION ONLY.
No model construction, no training, no forward passes, no refinement, no router
inference, no S_omega inference.  Every scientific number is reconstructed from the
frozen Phase25C OOF outcome table, the frozen Phase25E C8 memberships and the frozen
Phase25F C9 decision manifest.

Population: ROUTER_DEVELOPMENT (n=4957) only.
ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30 ; VAL808 = UNOPENED ; TEST = LOCKED.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- paths
ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TABLE = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"
CACHE25C = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
CACHE25E = ROOT / "data_cache" / "phase25e_barr_resource_gate_v1_0"
CACHE25F = ROOT / "data_cache" / "phase25f_barr_post_safety_v1_0"
CACHE25G = ROOT / "data_cache" / "phase25g_barr_integrated_eval_v1_0"
NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_25g_controlled_validation"

# ---------------------------------------------------------------------- constants
STRATA = ["BUSI", "ISIC", "KUB", "KVASIR"]
N_DEV = 4957
N_BOOT = 2000
SEED = 42
CI_PCT = (2.5, 97.5)

LAMBDAS = ["0.00", "0.25", "0.50", "1.00"]
BUDGETS = ["0.00", "0.10", "0.25", "0.50", "1.00"]
BUDGET_K = {"0.00": 0, "0.10": 495, "0.25": 1239, "0.50": 2478, "1.00": 4957}
BUDGET_LABEL = {"0.00": "0", "0.10": "10", "0.25": "25", "0.50": "50", "1.00": "100"}

GLOBAL_MACS = 31551740928
ROUTER_MACS = 36160
REFINER_MACS = 3230662656
SOMEGA_MACS = 1168
ACCOUNTING_LABEL = "ANALYTICAL MAC LOWER BOUND"

MARGIN = 0.005
BENEFICIAL_TH = 0.02
HARMFUL_TH = -0.01

C9_OUTCOMES = ("PRE_GATE_SKIP", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
EVIDENCE_CLASS = "CONTROLLED_META_LEVEL_OOF_DEVELOPMENT_EVIDENCE"

# --------------------------------------------------------------------------- SHAs
SHA = {
    "phase25c_oof_paired_gain_labels": "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f",
    "phase25e_policy_membership_manifest": "f4ff4b235c664339d237fd7ec51f948dbc233431a6fd45522bde2166327e679a",
    "phase24_router_split_manifest": "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
    "phase25e_bootstrap_plan_v1_0": "241ed5232b35709494adbf230151cec21259f86f88e1f06e5b2881a6d88f9b63",
    "phase25f_c9_decision_manifest": "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1",
    "phase25f_oof_safety_predictions": "a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee",
    "phase25e_evaluation_statistics_contract_v1_0": "fc90a1362a06eda342d987d2f6e1e12a1190ac650d7bb0db1234514a297644af",
    "phase25e_final_freeze": "e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e",
    "phase25f_final_freeze": "383280b9bbd015b8f85b962a453d7a14b40dea424b55b2fe3189d6bac127bb1c",
    "phase25f_final_freeze_notebook_compliance_addendum": None,  # filled at runtime
}

TERMINAL_SUCCESS = ("PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION_COMPLETE__"
                    "A7_A8_C8_C9_PRESERVATION_AND_H3_FROZEN__PHASE25_COMPLETE__"
                    "PHASE26_ELIGIBLE_NOT_STARTED")
TERMINAL_DRIFT = "PHASE25G_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT"
TERMINAL_RECON = "PHASE25G_BLOCKED__INTEGRATED_RECONSTRUCTION_FAILURE"
TERMINAL_STATS = "PHASE25G_BLOCKED__PAIRED_STATISTICS_INTEGRITY_FAILURE"
TERMINAL_NOTEBOOK = "PHASE25G_BLOCKED__REVIEWER_NOTEBOOK_INCOMPLETE"
TERMINAL_PHASE25_CLOSURE = "PHASE25G_COMPLETE_BUT_PHASE25_CLOSURE_BLOCKED__PROJECT_STATE_INCONSISTENT"

PREDECESSOR_TERMINAL = ("PHASE25G_SPEC_V1_1_COMPLETE__ROUTER_HOLDOUT_RESERVED_FOR_PHASE30__"
                        "DEV_ONLY_INTEGRATED_EVALUATION_FROZEN__PHASE25G_EXECUTION_ELIGIBLE_NOT_STARTED")


# ------------------------------------------------------------------------ IO utils
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


# ------------------------------------------------------------------------- loaders
def load_labels() -> pd.DataFrame:
    """Frozen Phase25C OOF paired-gain table in CANONICAL order (sample_id ascending)."""
    p = CACHE25C / "phase25c_oof_paired_gain_labels.csv"
    lab = pd.read_csv(p, dtype={"sample_id": str})
    lab = lab.sort_values("sample_id", kind="stable").reset_index(drop=True)
    return lab


def canonical_ids(lab: pd.DataFrame):
    return lab.sample_id.tolist()


def load_c8_memberships(ids):
    """Return (manifest_df_for_C8, dict pid -> membership record)."""
    man = pd.read_csv(TABLE / "phase25e_policy_membership_manifest.csv", dtype=str)
    man = man[man.comparator == "C8"].reset_index(drop=True)
    pol = {}
    for _, r in man.iterrows():
        pid = r["policy_id"]
        df = pd.read_csv(ROOT / r["membership_path"], dtype={"sample_id": str})
        if df.sample_id.tolist() != ids:
            raise ValueError(f"MEMBERSHIP_ORDER_MISMATCH:{pid}")
        pol[pid] = {
            "policy_id": pid,
            "lambda": r["lambda"],
            "budget": r["budget"],
            "K_b": int(r["K_b"]),
            "selected": df.selected.to_numpy().astype(bool),
            "action_available": df.action_available.to_numpy().astype(bool),
            "decision": df.decision.to_numpy(),
            "score": np.array([float(Fraction(s)) for s in df.routing_score_exact], dtype=np.float64),
            "membership_sha256": r["membership_sha256"],
            "selected_ids_sha256": r["selected_ids_sha256"],
            "membership_path": r["membership_path"],
        }
    return man, pol


def load_c9(ids):
    """Frozen Phase25F C9 decision manifest, grouped per policy and aligned to canonical order."""
    df = pd.read_csv(TABLE / "phase25f_c9_decision_manifest.csv",
                     dtype={"sample_id": str, "lambda": str, "budget": str})
    pos = {s: i for i, s in enumerate(ids)}
    out = {}
    for pid, g in df.groupby("policy_id", sort=False):
        g = g.copy()
        g["_pos"] = g.sample_id.map(pos)
        if g._pos.isna().any():
            raise ValueError(f"C9_SAMPLE_NOT_IN_CANONICAL:{pid}")
        g = g.sort_values("_pos", kind="stable")
        out[pid] = {
            "c9_outcome": g.c9_outcome.to_numpy(),
            "c9_state": g.c9_state.to_numpy(),
            "c8_decision": g.c8_decision.to_numpy(),
            "somega_decision": g.somega_decision.to_numpy(),
            "refiner_executed": g.refiner_executed.to_numpy().astype(int),
            "somega_executed": g.somega_executed.to_numpy().astype(int),
            "c9_final_prediction": g.c9_final_prediction.to_numpy(),
            "p_accept_oof": g.p_accept_oof.to_numpy(np.float64),
            "safety_logit_oof": g.safety_logit_oof.to_numpy(np.float64),
            "lambda": g["lambda"].to_numpy(),
            "budget": g["budget"].to_numpy(),
        }
    return df, out


def load_safety(ids):
    df = pd.read_csv(CACHE25F / "phase25f_oof_safety_predictions.csv", dtype={"sample_id": str})
    df = df.set_index("sample_id").loc[ids].reset_index()
    return df


def policy_id(lam, bud):
    return f"C8_lambda{lam}_budget{bud}"


# -------------------------------------------------------------------- group / boot
def build_group_index(ids):
    """Reconstruct the exact Phase25E CSR group index used to consume the frozen plan."""
    m = pd.read_csv(AUD / "phase24_router_split_manifest.csv",
                    usecols=["sample_id", "dataset", "group_key", "split_role"], dtype=str)
    dev = m[m.split_role == "ROUTER_DEVELOPMENT"]
    sid_pos = {s: i for i, s in enumerate(ids)}
    rows_by_group = {}
    for _, rr in dev.iterrows():
        rows_by_group.setdefault(rr["group_key"], []).append(sid_pos[rr["sample_id"]])
    group_lists = {d: sorted(dev.loc[dev.dataset == d, "group_key"].unique()) for d in STRATA}
    csr = {}
    for d in STRATA:
        segs, sizes = [], []
        for g in group_lists[d]:
            arr = np.array(sorted(rows_by_group[g]), dtype=np.int64)
            segs.append(arr)
            sizes.append(len(arr))
        csr[d] = {
            "flat": np.concatenate(segs),
            "sizes": np.array(sizes, dtype=np.int64),
            "starts": np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int64),
        }
    return csr, group_lists


def load_plan(plan_path=None):
    """Load the frozen Phase25E bootstrap plan once into a plain dict of arrays."""
    plan_path = plan_path or (CACHE25E / "phase25e_bootstrap_plan_v1_0.npz")
    z = np.load(plan_path)
    return {k: z[k] for k in z.files}


def iter_bootstrap_indices(csr, plan=None):
    """Yield (b, idx) replaying the EXACT frozen Phase25E draws."""
    if plan is None:
        plan = load_plan()
    for b in range(N_BOOT):
        parts = []
        for d in STRATA:
            c = csr[d]
            draws = plan[f"{b}:{d}"]
            counts = c["sizes"][draws]
            rep_starts = np.repeat(c["starts"][draws], counts)
            seg = np.repeat(np.cumsum(counts) - counts, counts)
            pos = np.arange(rep_starts.size) - seg
            parts.append(c["flat"][rep_starts + pos])
        yield b, np.concatenate(parts)


# ------------------------------------------------------------------------ metrics
def replicate_select(score, idx, k_rep):
    """Re-apply the frozen policy ranking to a resampled eligible multiset."""
    if k_rep == 0:
        return np.zeros(idx.size, dtype=bool)
    pos_r = idx
    sc_r = score[idx]
    rank_r = np.lexsort((pos_r, -sc_r))
    sel = np.zeros(idx.size, dtype=bool)
    sel[rank_r[:k_rep]] = True
    return sel


def arm_final_delta(sel, accept, d):
    """A7 = selected * d ; A8 = accepted * d (accept implies selected)."""
    a7 = np.where(sel, d, 0.0)
    a8 = np.where(accept, d, 0.0)
    return a7, a8


def domain_means(values, dom_idx):
    out = {}
    for d in STRATA:
        m = dom_idx[d]
        if m.sum() > 0:
            out[d] = float(values[m].mean())
        else:
            out[d] = None
    return out


def macro(vals):
    present = [v for v in vals if v is not None]
    return float(np.mean(present)) if present else None


def safe_div(a, b):
    return None if (b is None or b == 0) else a / b


def paired_p(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() == 0:
        return None, None, None
    D = a[m] - b[m]
    B = D.size
    p_lower = (1 + int((D <= 0).sum())) / (B + 1)
    p_upper = (1 + int((D >= 0).sum())) / (B + 1)
    p = min(1.0, 2 * min(p_lower, p_upper))
    return float(D.mean()), p, B


def ci(arr, pct=CI_PCT):
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None, None, None, 0
    return (float(np.mean(finite)),
            float(np.percentile(finite, pct[0])),
            float(np.percentile(finite, pct[1])),
            int(finite.size))


# ------------------------------------------------------------------ point metrics
def point_policy_metrics(pid, rec, c9rec, lab, dom_idx):
    """Full §14 point metrics for one policy on the frozen DEV population."""
    d = lab.delta_dice.to_numpy(np.float64)
    gd = lab.global_dice.to_numpy(np.float64)
    crd = lab.candidate_refined_dice.to_numpy(np.float64)
    cat = lab.gain_category.to_numpy()

    sel = rec["selected"]
    out = c9rec["c9_outcome"]
    accept = out == "EXECUTE_THEN_ACCEPT"
    reject = out == "EXECUTE_THEN_REJECT"
    skip = out == "PRE_GATE_SKIP"

    a7d, a8d = arm_final_delta(sel, accept, d)
    K = int(sel.sum())

    a7_dice = gd + a7d
    a8_dice = gd + a8d
    g_dom = domain_means(gd, dom_idx)
    g_macro = macro(list(g_dom.values()))
    a7_dom = domain_means(a7d, dom_idx)
    a8_dom = domain_means(a8d, dom_idx)
    a7_macro = macro(list(a7_dom.values()))
    a8_macro = macro(list(a8_dom.values()))

    neg = d < 0
    harm_a7 = sel & neg
    harm_a8 = accept & neg
    harm_prevented = reject & neg

    # per-domain harmful replacement counts
    a7_harm_dom = {dd: int((harm_a7 & dom_idx[dd]).sum()) for dd in STRATA}
    a8_harm_dom = {dd: int((harm_a8 & dom_idx[dd]).sum()) for dd in STRATA}
    sel_dom = {dd: int((sel & dom_idx[dd]).sum()) for dd in STRATA}
    acc_dom = {dd: int((accept & dom_idx[dd]).sum()) for dd in STRATA}
    rej_dom = {dd: int((reject & dom_idx[dd]).sum()) for dd in STRATA}
    dom_n = {dd: int(dom_idx[dd].sum()) for dd in STRATA}

    return {
        "policy_id": pid,
        "lambda": rec["lambda"],
        "budget": rec["budget"],
        "membership_equivalence_group": rec["budget"],
        "n": int(d.size),
        "selected_count": K,
        "executed_count": K,
        "activation_fraction": K / d.size,
        # ---- A7
        "A7_mean_dice": float(a7_dice.mean()),
        "A7_delta_vs_global": float(a7d.mean()),
        "A7_macro_domain_mean_dice": a7_macro,
        "A7_macro_domain_delta_vs_global": a7_macro,
        "A7_harmful_replacement_count": int(harm_a7.sum()),
        "A7_harmful_replacement_rate": safe_div(int(harm_a7.sum()), K),
        "A7_fallback_count": 0,
        "A7_fallback_rate": 0.0 if K else None,
        # ---- A8
        "A8_mean_dice": float(a8_dice.mean()),
        "A8_delta_vs_global": float(a8d.mean()),
        "A8_macro_domain_mean_dice": a8_macro,
        "A8_macro_domain_delta_vs_global": a8_macro,
        "A8_harmful_replacement_count": int(harm_a8.sum()),
        "A8_harmful_replacement_rate": safe_div(int(harm_a8.sum()), K),
        "A8_fallback_count": int(reject.sum()),
        "A8_fallback_rate": safe_div(int(reject.sum()), K),
        "A8_accept_count": int(accept.sum()),
        "A8_accept_rate_among_executed": safe_div(int(accept.sum()), K),
        "A8_reject_count": int(reject.sum()),
        "A8_reject_rate_among_executed": safe_div(int(reject.sum()), K),
        "A8_skip_count": int(skip.sum()),
        # ---- A8 - A7
        "A8_minus_A7": float((a8d - a7d).mean()),
        "A8_minus_A7_macro_domain": (None if (a7_macro is None or a8_macro is None)
                                     else float(a8_macro - a7_macro)),
        "harm_prevented": int(harm_prevented.sum()),
        "A7_harmful_replacement_rate_minus_A8": (
            None if K == 0 else float((int(harm_a7.sum()) - int(harm_a8.sum())) / K)),
        # ---- compute
        "A7_avg_analytical_macs": GLOBAL_MACS + ROUTER_MACS + (K / d.size) * REFINER_MACS,
        "A8_avg_analytical_macs": GLOBAL_MACS + ROUTER_MACS + (K / d.size) * (REFINER_MACS + SOMEGA_MACS),
        "A8_minus_A7_macs": (K / d.size) * SOMEGA_MACS,
        # ---- cross-check anchors
        "_global_dice_mean": float(gd.mean()),
        "_global_macro_dice": g_macro,
        "_global_dom": g_dom,
        "_a7_dom": a7_dom,
        "_a8_dom": a8_dom,
        "_a7_harm_dom": a7_harm_dom,
        "_a8_harm_dom": a8_harm_dom,
        "_sel_dom": sel_dom,
        "_acc_dom": acc_dom,
        "_rej_dom": rej_dom,
        "_domain_n": dom_n,
        "_a7d": a7d,
        "_a8d": a8d,
        "_selected": sel,
        "_accept": accept,
        "_reject": reject,
        "_candidate_refined_dice": crd,
        "_gain_category": cat,
    }
