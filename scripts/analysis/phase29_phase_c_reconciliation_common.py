"""Phase 29 Phase C post-execution reconciliation - shared helpers.

ARTIFACT-LEVEL ONLY. No training, no model forward, no OOF prediction,
no VAL808 / ROUTER_HOLDOUT / TEST access. This module only reads frozen
Phase29 Phase-C/D artifacts and recomputes metric summaries from frozen
membership + outcome tables.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDITS = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
DATACACHE = ROOT / "data_cache"

MASTER_SEEDS = [42, 123, 3407]
OOF_K = 1239
N_DEV = 4957
N_VAL808 = 808

# Frozen Phase25E router semantic thresholds.
BENEFICIAL_TAU = 0.02      # BENEFICIAL iff d_i >= +0.02
HARMFUL_TAU = -0.01        # HARMFUL   iff d_i <= -0.01
BUDGET_FRACTION = 0.25     # precision_at_budget = 25% -> K = 1239

# Exact rationals (frozen).
CAL_C = (1051648, 10270749)
CAL_LAMBDA = (0.25 * 1051648, 10270749)

EXECUTION_FROZEN_FLAGS = {
    "training_changed": False,
    "checkpoints_changed": False,
    "OOF_predictions_changed": False,
    "memberships_changed": False,
    "DeltaDice_targets_changed": False,
    "integrated_predictions_changed": False,
    "macro_DEV_Dice_changed": False,
    "VAL808_opened": False,
}

CLASSIFICATION = "ARTIFACT_LEVEL_METRIC_AND_EXECUTION_CONTRACT_REPAIR_ONLY"
SUCCESS_TERMINAL = (
    "PHASE29_PHASE_C_RECONCILED__ROUTER_METRIC_SEMANTICS_PHASE27_VAL808_NUMERICS_"
    "AND_ENTRYPOINT_EXCEPTION_FROZEN__PHASE_D_ELIGIBLE_NOT_STARTED"
)
PHASE_C_SCIENTIFIC_TERMINAL = (
    "PHASE29_PHASE_C_NEW_SEED_TRAINING_COMPLETE__32_RUNS_AND_THREE_SEED_DEV_"
    "REPRODUCIBILITY_FROZEN__PRE_VAL808_GATE_PASS"
)

BLOCKED_TERMINALS = [
    "PHASE29_PHASE_C_REPAIR_BLOCKED__INTEGRATED_DEV_RESULT_DRIFT",
    "PHASE29_PHASE_C_REPAIR_BLOCKED__CANONICAL_TRAINER_DRIFT_EXCEEDS_DECLARED_EXCEPTION",
    "PHASE29_PHASE_C_REPAIR_BLOCKED__ROUTER_METRIC_ARITHMETIC_MAXIMUM_VIOLATED",
    "PHASE29_PHASE_C_REPAIR_BLOCKED__FROZEN_MEMBERSHIP_UNAVAILABLE",
    "PHASE29_PHASE_C_REPAIR_BLOCKED__PHASE27_NUMERIC_CONTRACT_UNREADABLE",
    "PHASE29_PHASE_C_REPAIR_BLOCKED__ENTRYPOINT_DIFF_NOT_EXACTLY_TWO_TOKENS",
    "PHASE29_PHASE_C_REPAIR_BLOCKED__SEED123_3407_TRAINING_OUTPUT_INCONSISTENT",
]


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_csv_dicts(path):
    import csv

    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, header, rows):
    import csv

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def seed_cache_dir(seed):
    return DATACACHE / f"phase29_seed{seed}"


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def sample_sd(xs):
    """Sample standard deviation, ddof=1."""
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


# ---------------------------------------------------------------------------
# Frozen Phase25E router metric semantics (bind verbatim).
# ---------------------------------------------------------------------------
def phase25e_router_metrics(selected_ids, delta_by_id):
    """Compute frozen Phase25E router metrics from frozen membership + DeltaDice.

    S = selected/routed set, E = eligible set (all candidates with a true
    DeltaDice available = full DEV OOF population), d_i = true seed-specific
    DeltaDice, B = {i in E : d_i >= +0.02}, H = {i in E : d_i <= -0.01},
    K = |S|.
    """
    E = set(delta_by_id.keys())
    S = [i for i in selected_ids if i in E]
    K = len(S)

    B = {i for i in E if delta_by_id[i] >= BENEFICIAL_TAU}
    H = {i for i in E if delta_by_id[i] <= HARMFUL_TAU}

    S_set = set(S)
    n_beneficial_routed = len(S_set & B)
    n_harmful_routed = len(S_set & H)

    denom_pos = sum(max(delta_by_id[i], 0.0) for i in E)
    num_pos = sum(max(delta_by_id[i], 0.0) for i in S)

    return {
        "K": K,
        "n_eligible": len(E),
        "n_beneficial_total": len(B),
        "n_harmful_total": len(H),
        "n_beneficial_routed": n_beneficial_routed,
        "n_harmful_routed": n_harmful_routed,
        "precision_at_budget": (n_beneficial_routed / K) if K else float("nan"),
        "precision_at_25pct": (n_beneficial_routed / K) if K else float("nan"),
        "benefit_capture_at_budget": (num_pos / denom_pos) if denom_pos else float("nan"),
        "benefit_capture": (num_pos / denom_pos) if denom_pos else float("nan"),
        "mean_true_delta_dice_among_routed": (sum(delta_by_id[i] for i in S) / K)
        if K
        else float("nan"),
        "beneficial_coverage": (n_beneficial_routed / len(B)) if B else float("nan"),
        "missed_benefit_rate": (len(B - S_set) / len(B)) if B else float("nan"),
        "harmful_activation_rate": (n_harmful_routed / K) if K else float("nan"),
        "beneficial_activation_rate": (n_beneficial_routed / len(B)) if B else float("nan"),
        "harmful_activation_share": (n_harmful_routed / K) if K else float("nan"),
    }
