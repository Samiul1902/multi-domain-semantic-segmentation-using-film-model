"""Paired comparisons with declared resampling units and declared inference class.

Three things this module refuses to do, because the repository's own frozen
protocol forbids them:

1. **Treat seeds as independent replicates.** The three seeds are not three
   independent draws of the same quantity for historical FULL downstream
   components: historical seeds 123 and 3407 reuse the seed-42 G. The new FULL
   producer trains independent G/R/B/S families, whose identity is verified
   separately. Seed variability here is a spread, never a standard error.
2. **Treat images as independent when they are clustered.** Where a
   ``patient_id``/``group_key`` exists, the bootstrap resamples **clusters**, not
   images.  The resampling unit is written into every result.
3. **Produce a confirmatory p-value.** No paired p-value procedure is frozen for
   these comparisons.  ``docs/phase30_final_development_validation_spec_v1_3.md``
   §B records that the claim-bearing inference is *point estimate + 95% CI only*
   (``no_p_value_gating_for_primary = true``), and §C that the frozen
   non-inferiority gate is ``lower 95% CI > -0.005`` and is **not** a test against
   zero.  So every result here is ``EXPLORATORY_UNCERTAINTY_ONLY`` and no p-value
   is computed.  :func:`assert_no_confirmatory_claim` enforces that.

Nothing here decides that a model improved.  A point estimate with a CI that
excludes zero is still reported as *a descriptive difference*, and
``claim_status`` stays ``NO_CLAIM``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from src.metrics import evaluation_metrics as EM

from . import protocol as P

# --------------------------------------------------------------------------- #
# Inference class
# --------------------------------------------------------------------------- #
EXPLORATORY = "EXPLORATORY_UNCERTAINTY_ONLY"
CONFIRMATORY = "PROTOCOL_SPECIFIED_CONFIRMATORY"

#: Read from docs/phase30_final_development_validation_spec_v1_3.md §C.
NON_INFERIORITY_MARGIN = -0.005
NON_INFERIORITY_PROVENANCE = (
    "docs/phase30_final_development_validation_spec_v1_3.md §C: 'The claim remains "
    "lower 95% CI > -0.005'; §B: no paired p-value procedure is frozen, "
    "no_p_value_gating_for_primary = true")

#: No frozen statistical protocol authorizes a confirmatory test for the Phase C
#: comparisons, so the evaluator does not perform one.
CONFIRMATORY_AUTHORIZED = False
CONFIRMATORY_BLOCK_REASON = (
    "No frozen statistical protocol defines a confirmatory hypothesis test for the "
    "eight-model comparison. The Phase-30 specification authorizes a point estimate "
    "plus a 95% CI and a non-inferiority bound for the preservation claim only, and "
    "sets no_p_value_gating_for_primary = true. A p-value here would be an invented "
    "procedure, so none is produced.")

CLAIM_STATUS = "NO_CLAIM"
DEFAULT_N_BOOT = 2000
DEFAULT_SEED = 20261103


class StatisticsError(RuntimeError):
    pass


class PairingError(StatisticsError):
    pass


class ConfirmatoryNotAuthorized(StatisticsError):
    pass


# --------------------------------------------------------------------------- #
# Pairing
# --------------------------------------------------------------------------- #
def _index(records: Iterable[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    out: Dict[str, Mapping[str, Any]] = {}
    for record in records:
        key = str(record["sample_id"])
        if key in out:
            raise PairingError(f"duplicate sample_id {key!r} in one cell")
        out[key] = record
    return out


def pair_records(a: Sequence[Mapping[str, Any]],
                 b: Sequence[Mapping[str, Any]]) -> List[Tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Align two cells on identical sample IDs, in a deterministic order.

    A mismatch is an error, never a silent inner join: comparing different image
    sets is not a paired comparison.
    """
    ia, ib = _index(a), _index(b)
    if set(ia) != set(ib):
        only_a, only_b = sorted(set(ia) - set(ib))[:5], sorted(set(ib) - set(ia))[:5]
        raise PairingError(f"sample sets differ: only_a={only_a} only_b={only_b}")
    return [(ia[k], ib[k]) for k in sorted(ia)]


def _cluster_of(record: Mapping[str, Any], unit: str) -> str:
    if unit == "image":
        return str(record["sample_id"])
    if unit == "patient":
        value = record.get("patient_id")
    elif unit == "group":
        value = record.get("group_key")
    else:
        raise StatisticsError(f"unknown resampling unit {unit!r}")
    if value is None or str(value) in ("", "NOT_AVAILABLE", "None"):
        raise StatisticsError(
            f"resampling unit {unit!r} requested but the record carries no {unit} identifier; "
            "falling back to images would understate the interval")
    return str(value)


# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #
def cluster_bootstrap_ci(differences: Sequence[float], clusters: Sequence[str], *,
                         n_boot: int = DEFAULT_N_BOOT, seed: int = DEFAULT_SEED,
                         alpha: float = 0.05, statistic: str = "mean") -> Dict[str, Any]:
    """Percentile bootstrap resampling **clusters**, not observations.

    Every cluster keeps all of its images in a resample, so within-cluster
    correlation is preserved and the interval is not artificially narrow.
    """
    d = np.asarray(differences, dtype=np.float64)
    c = np.asarray(clusters, dtype=object)
    if d.ndim != 1 or c.ndim != 1 or not d.size:
        raise StatisticsError("nonempty one-dimensional differences and cluster labels required")
    if isinstance(n_boot, bool) or not isinstance(n_boot, (int, np.integer)) or n_boot < 1:
        raise StatisticsError("n_boot must be a positive integer")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise StatisticsError("alpha must be finite and strictly between zero and one")
    if statistic not in {"mean", "median"}:
        raise StatisticsError("statistic must be mean or median")
    if any(not isinstance(label, str) or not label.strip() for label in c):
        raise StatisticsError("cluster labels must be nonempty strings")
    if d.shape != c.shape:
        raise StatisticsError(f"{len(d)} differences vs {len(c)} cluster labels")
    if not np.isfinite(d).all():
        raise StatisticsError("differences contain non-finite values")

    names = sorted(set(c.tolist()))
    if len(names) == 1:
        return {"estimate": float(d.mean()) if statistic == "mean" else float(np.median(d)),
                "ci_low": float("nan"), "ci_high": float("nan"),
                "n": int(d.size), "n_clusters": 1, "resampling_unit": "cluster",
                "ci_method": "percentile_cluster_bootstrap", "n_boot": int(n_boot),
                "seed": int(seed), "alpha": float(alpha),
                "degenerate_reason": "only one cluster; a cluster bootstrap has no spread"}

    members = {name: np.flatnonzero(c == name) for name in names}
    rng = np.random.default_rng(seed)
    stats = np.empty(int(n_boot), dtype=np.float64)
    for b in range(int(n_boot)):
        pick = rng.integers(0, len(names), size=len(names))
        idx = np.concatenate([members[names[i]] for i in pick])
        stats[b] = d[idx].mean() if statistic == "mean" else np.median(d[idx])
    return {"estimate": float(d.mean()) if statistic == "mean" else float(np.median(d)),
            "ci_low": float(np.percentile(stats, 100 * alpha / 2)),
            "ci_high": float(np.percentile(stats, 100 * (1 - alpha / 2))),
            "n": int(d.size), "n_clusters": len(names),
            "resampling_unit": "cluster", "ci_method": "percentile_cluster_bootstrap",
            "n_boot": int(n_boot), "seed": int(seed), "alpha": float(alpha)}


def paired_ci(differences: Sequence[float], clusters: Optional[Sequence[str]] = None, *,
              unit: str = "image", n_boot: int = DEFAULT_N_BOOT, seed: int = DEFAULT_SEED,
              alpha: float = 0.05) -> Dict[str, Any]:
    """Route to the image bootstrap or the cluster bootstrap, and say which."""
    if unit == "image":
        out = EM.bootstrap_ci(list(differences), n_boot=n_boot, seed=seed, alpha=alpha,
                              resampling_unit="image")
        out["n"] = len(differences)
        out["n_clusters"] = len(differences)
        out["ci_method"] = "percentile_image_bootstrap"
        out["mean_difference"] = out["estimate"]
        return out
    if clusters is None:
        raise StatisticsError(f"unit {unit!r} requires cluster identifiers")
    return cluster_bootstrap_ci(differences, clusters, n_boot=n_boot, seed=seed, alpha=alpha)


# --------------------------------------------------------------------------- #
# One comparison
# --------------------------------------------------------------------------- #
def compare_pair(model_a: str, model_b: str, seed: int,
                 records_a: Sequence[Mapping[str, Any]],
                 records_b: Sequence[Mapping[str, Any]], *,
                 metric: str = "dice", unit: str = "image",
                 n_boot: int = DEFAULT_N_BOOT, bootstrap_seed: int = DEFAULT_SEED,
                 domain: Optional[str] = None) -> Dict[str, Any]:
    """Paired ``a - b`` on identical images.  Descriptive, never confirmatory."""
    pairs = pair_records(records_a, records_b)
    if domain is not None:
        pairs = [(x, y) for x, y in pairs if x["domain"] == domain]
        if not pairs:
            return {"status": "NOT_APPLICABLE", "reason": f"no paired images in {domain}"}

    diffs, clusters = [], []
    for x, y in pairs:
        va, vb = x.get(metric), y.get(metric)
        if va is None or vb is None:
            continue
        if not (np.isfinite(float(va)) and np.isfinite(float(vb))):
            continue
        diffs.append(float(va) - float(vb))
        clusters.append(_cluster_of(x, unit))
    if not diffs:
        return {"status": "NOT_APPLICABLE",
                "reason": f"no finite paired {metric} values"}

    ci = paired_ci(diffs, clusters, unit=unit, n_boot=n_boot, seed=bootstrap_seed)
    return {
        "status": "DESCRIPTIVE",
        "comparison": f"{model_a} minus {model_b}",
        "model_a": model_a, "model_b": model_b, "seed": int(seed),
        "metric": metric, "domain": domain,
        "n_paired_images": len(diffs),
        "mean_difference": float(np.mean(diffs)),
        "median_difference": float(np.median(diffs)),
        "ci_low": ci["ci_low"], "ci_high": ci["ci_high"],
        "ci_method": ci["ci_method"], "resampling_unit": ci["resampling_unit"],
        "n_clusters": ci["n_clusters"], "n_boot": ci["n_boot"],
        "bootstrap_seed": int(bootstrap_seed), "alpha": ci["alpha"],
        "inference_class": EXPLORATORY,
        "p_value": None,
        "p_value_reason": CONFIRMATORY_BLOCK_REASON,
        "claim_status": CLAIM_STATUS,
        "improvement_claimed": False,
        "note": ("Point estimate and 95% CI only. A CI that excludes zero is a "
                 "descriptive difference, not a demonstrated improvement."),
    }


def domain_differences(model_a: str, model_b: str, seed: int,
                       records_a: Sequence[Mapping[str, Any]],
                       records_b: Sequence[Mapping[str, Any]], *,
                       metric: str = "dice", unit: str = "image") -> Dict[str, Any]:
    return {domain: compare_pair(model_a, model_b, seed, records_a, records_b,
                                 metric=metric, unit=unit, domain=domain)
            for domain in P.DOMAINS}


# --------------------------------------------------------------------------- #
# Seed aggregation
# --------------------------------------------------------------------------- #
SEED_NOTE = (
    "The three seeds are not independent replicates of the FULL downstream "
    "components: seeds 123 and 3407 reuse the seed-42 G. The spread below is a "
    "descriptive seed variability, never a standard error, and never a basis for "
    "inference.")


def seed_summary(values: Sequence[float], *, label: str = "") -> Dict[str, Any]:
    arr = np.asarray([v for v in values if v is not None and np.isfinite(float(v))],
                     dtype=np.float64)
    if arr.size == 0:
        return {"label": label, "n_seeds": 0, "mean": None, "sd": None,
                "inference_class": EXPLORATORY, "note": SEED_NOTE}
    return {"label": label, "n_seeds": int(arr.size), "mean": float(arr.mean()),
            "sd": float(arr.std(ddof=1)) if arr.size > 1 else None,
            "min": float(arr.min()), "max": float(arr.max()),
            "inference_class": EXPLORATORY, "note": SEED_NOTE}


# --------------------------------------------------------------------------- #
# Non-inferiority (declared, gated, never automatic)
# --------------------------------------------------------------------------- #
def evaluate_non_inferiority(ci_low: Optional[float], *,
                            protocol_reference: str = "") -> Dict[str, Any]:
    """Apply the frozen bound **only** when the caller names the protocol row.

    This does not decide anything on its own: it returns the verdict against the
    frozen margin together with the reference, and the caller still has to decide
    whether that comparison is the one the protocol scopes the bound to.

    ``protocol_reference`` defaults to the empty string so that omitting it raises
    the explicit :class:`ConfirmatoryNotAuthorized` below rather than a bare
    ``TypeError`` from the signature — the refusal is then legible and carries its
    reason.
    """
    if not protocol_reference:
        raise ConfirmatoryNotAuthorized(
            "the non-inferiority bound may only be evaluated with an explicit protocol reference")
    if ci_low is None or not np.isfinite(float(ci_low)):
        return {"verdict": "NOT_EVALUABLE", "margin": NON_INFERIORITY_MARGIN,
                "protocol_reference": protocol_reference,
                "provenance": NON_INFERIORITY_PROVENANCE}
    met = float(ci_low) > NON_INFERIORITY_MARGIN
    return {"verdict": "BOUND_MET" if met else "BOUND_NOT_MET",
            "ci_low": float(ci_low), "margin": NON_INFERIORITY_MARGIN,
            "protocol_reference": protocol_reference,
            "provenance": NON_INFERIORITY_PROVENANCE,
            "note": ("This is the frozen preservation bound, not a test against zero "
                     "and not a superiority claim.")}


def assert_no_confirmatory_claim(result: Mapping[str, Any]) -> None:
    """Guard used by the report layer: nothing may carry a p-value or a claim."""
    if result.get("p_value") is not None:
        raise ConfirmatoryNotAuthorized("a p-value may not be produced without a frozen procedure")
    if result.get("improvement_claimed"):
        raise ConfirmatoryNotAuthorized("an improvement claim may not be auto-generated")
    if result.get("inference_class") == CONFIRMATORY and not CONFIRMATORY_AUTHORIZED:
        raise ConfirmatoryNotAuthorized(CONFIRMATORY_BLOCK_REASON)


# --------------------------------------------------------------------------- #
# The comparison set the mission enumerates
# --------------------------------------------------------------------------- #
def build_comparisons(cells: Mapping[Tuple[str, int], Sequence[Mapping[str, Any]]], *,
                      unit: str = "image", n_boot: int = DEFAULT_N_BOOT,
                      bootstrap_seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """FULL vs Global, FULL vs Lite, FULL vs each baseline, Lite vs each baseline.

    Only pairs that actually have both cells are computed; the rest are reported
    ``NOT_AVAILABLE`` with the reason, never imputed.
    """
    from . import registry as REG

    def get(model: str, seed: int):
        return cells.get((model, seed))

    def run(a: str, b: str, seeds: Sequence[int]) -> Dict[str, Any]:
        per_seed = {}
        for seed in seeds:
            ra, rb = get(a, seed), get(b, seed)
            if ra is None or rb is None:
                per_seed[str(seed)] = {"status": "NOT_AVAILABLE",
                                       "reason": "one or both cells absent"}
                continue
            per_seed[str(seed)] = compare_pair(a, b, seed, ra, rb, unit=unit,
                                               n_boot=n_boot, bootstrap_seed=bootstrap_seed)
        means = [v["mean_difference"] for v in per_seed.values()
                 if v.get("status") == "DESCRIPTIVE"]
        return {"comparison": f"{a} minus {b}", "per_seed": per_seed,
                "seed_summary": seed_summary(means, label=f"{a} minus {b}"),
                "inference_class": EXPLORATORY, "claim_status": CLAIM_STATUS}

    available_seeds = sorted({s for (_m, s) in cells})
    return {
        "full_vs_global": run(REG.FULL, REG.GLOBAL, available_seeds),
        "full_vs_lite": run(REG.FULL, REG.LITE, available_seeds),
        "full_vs_baselines": {b: run(REG.FULL, b, available_seeds) for b in REG.BASELINES},
        "lite_vs_baselines": {b: run(REG.LITE, b, available_seeds) for b in REG.BASELINES},
        "inference_class": EXPLORATORY,
        "confirmatory_authorized": CONFIRMATORY_AUTHORIZED,
        "confirmatory_block_reason": CONFIRMATORY_BLOCK_REASON,
        "resampling_unit": unit,
        "claim_status": CLAIM_STATUS,
    }


def comparison_fingerprint(payload: Mapping[str, Any]) -> str:
    """Stable digest of a comparison block, for provenance."""
    import json

    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


__all__ = ["CLAIM_STATUS", "CONFIRMATORY", "CONFIRMATORY_AUTHORIZED",
           "CONFIRMATORY_BLOCK_REASON", "ConfirmatoryNotAuthorized", "EXPLORATORY",
           "NON_INFERIORITY_MARGIN", "NON_INFERIORITY_PROVENANCE", "PairingError",
           "SEED_NOTE", "StatisticsError", "assert_no_confirmatory_claim",
           "build_comparisons", "cluster_bootstrap_ci", "compare_pair",
           "comparison_fingerprint", "domain_differences", "evaluate_non_inferiority",
           "pair_records", "paired_ci", "seed_summary"]
