"""Paired case/cluster statistics; never resamples pixels or training seeds."""
from __future__ import annotations

import numpy as np
from . import DOMAINS


def describe(values):
    v = np.asarray(values, dtype=float)
    if v.ndim != 1:
        raise ValueError("one-dimensional values required")
    if np.isinf(v).any():
        raise ValueError("infinite values forbidden")
    good = v[np.isfinite(v)]
    return {"n_total": int(v.size), "n_missing": int(v.size - good.size), "n_observed": int(good.size),
            "mean": float(good.mean()) if good.size else None, "median": float(np.median(good)) if good.size else None,
            "sample_sd": float(good.std(ddof=1)) if good.size > 1 else None,
            "minimum": float(good.min()) if good.size else None, "maximum": float(good.max()) if good.size else None}


def adjust_pvalues(values, method="holm"):
    p = np.asarray(values, dtype=float)
    if p.ndim != 1 or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("finite p-values in [0,1] required")
    if method not in ("holm", "bonferroni", "bh"):
        raise ValueError("unknown method")
    n = len(p)
    if not n:
        return []
    order = np.argsort(p, kind="stable")
    ranked = p[order]
    if method == "holm":
        adjusted = np.maximum.accumulate(ranked * np.arange(n, 0, -1))
    elif method == "bh":
        adjusted = np.minimum.accumulate((ranked * n / np.arange(1, n + 1))[::-1])[::-1]
    else:
        adjusted = ranked * n
    out = np.empty(n)
    out[order] = np.minimum(adjusted, 1)
    return out.tolist()


def paired_bootstrap(rows, *, seeds, domains=DOMAINS, n_boot=10000, rng_seed=20261027,
                     confidence=0.95, patient_domains=("KUB",)):
    """Equal-domain, equal-seed paired mean; shared draws across fixed seeds.

    Each row has domain, sample_id, seed, treatment, control and patient_id.
    Resample patients within specified domains, cases elsewhere; all images in
    each sampled cluster retained with multiplicity. Missing/duplicate/nonfinite
    observations abort. Generic utility; C1 use requires frozen input/plan audit.
    """
    domains, seeds = tuple(domains), tuple(seeds)
    if any(d not in domains for d in patient_domains):
        raise ValueError("patient domains must be declared analysis domains")
    if not domains or len(set(domains)) != len(domains) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("unique nonempty domains and seeds required")
    if type(n_boot) is not int or n_boot < 1 or not 0 < confidence < 1:
        raise ValueError("invalid bootstrap settings")
    data = {}
    for r in rows:
        d, s, sid = r["domain"], r["seed"], r["sample_id"]
        if r.get("split") is not None and r["split"] not in {"TRAIN", "VAL", "SYNTHETIC"}:
            raise ValueError("prohibited analysis split")
        if d not in domains or s not in seeds or not isinstance(sid, str) or not sid:
            raise ValueError("unexpected domain, seed or sample")
        key = (d, sid, s)
        if key in data:
            raise ValueError("duplicate paired observation")
        a, b = float(r["treatment"]), float(r["control"])
        if not np.isfinite(a) or not np.isfinite(b):
            raise ValueError("missing or nonfinite paired observation")
        patient = r.get("patient_id")
        if d in patient_domains and (not isinstance(patient, str) or not patient.strip() or patient.upper() == "NOT_AVAILABLE"):
            raise ValueError("required patient ID missing")
        data[key] = (a - b, patient)
    groups, per_seed = {}, []
    for d in domains:
        samples = sorted({sid for dom, sid, _ in data if dom == d})
        if not samples:
            raise ValueError("missing domain")
        clusters = {}
        for sid in samples:
            vals = [data.get((d, sid, s)) for s in seeds]
            if any(v is None for v in vals) or len({v[1] for v in vals}) != 1:
                raise ValueError("incomplete seeds or inconsistent patient grouping")
            cluster = vals[0][1] if d in patient_domains else sid
            clusters.setdefault(cluster, []).append([v[0] for v in vals])
        groups[d] = [np.asarray(clusters[k], dtype=float) for k in sorted(clusters)]
    for j in range(len(seeds)):
        per_seed.append(float(np.mean([np.concatenate(groups[d], axis=0)[:, j].mean() for d in domains])))
    rng = np.random.Generator(np.random.PCG64(rng_seed))
    draws = np.empty(n_boot)
    for b in range(n_boot):
        domain_values = []
        for d in domains:
            clusters = groups[d]
            picked = rng.integers(0, len(clusters), size=len(clusters))
            domain_values.append(float(np.concatenate([clusters[i] for i in picked], axis=0).mean(axis=0).mean()))
        draws[b] = np.mean(domain_values)
    alpha = (1 - confidence) / 2
    return {"estimate": float(np.mean(per_seed)), "per_seed": dict(zip(map(str, seeds), per_seed)),
            "seed_descriptive": describe(per_seed), "ci": [float(np.quantile(draws, alpha)), float(np.quantile(draws, 1 - alpha))],
            "ci_method": "domain_stratified_paired_cluster_percentile", "confidence": confidence,
            "resamples": n_boot, "rng": "PCG64", "rng_seed": rng_seed,
            "patient_domains": list(patient_domains), "other_domains_unit": "image",
            "uncertainty": "conditional on fixed seeds; case/cluster sampling only; no seed inference",
            "cluster_counts": {d: len(groups[d]) for d in domains}, "n_paired_rows": len(data),
            "n_missing": 0, "effect_size": "mean paired difference in input metric units",
            "bootstrap_distribution_sd": float(draws.std(ddof=1)) if n_boot > 1 else None,
            "per_domain_seed_effects": {d: {str(s): float(np.concatenate(groups[d], axis=0)[:, j].mean()) for j, s in enumerate(seeds)} for d in domains}}


def paired_summary(treatment, control):
    """Descriptive complete pairs, with explicit missing-pair accounting."""
    a, b = np.asarray(treatment, dtype=float), np.asarray(control, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or np.isinf(a).any() or np.isinf(b).any():
        raise ValueError("matching one-dimensional finite-or-NaN arrays required")
    valid = np.isfinite(a) & np.isfinite(b)
    differences = a[valid] - b[valid]
    result = describe(differences)
    result.update({"n_improved": int(np.count_nonzero(differences > 0)),
                   "n_harmed": int(np.count_nonzero(differences < 0)),
                   "n_unchanged": int(np.count_nonzero(differences == 0)),
                   "n_expected_pairs": int(a.size), "n_missing_pairs": int((~valid).sum()),
                   "effect_size": "mean paired difference in metric units"})
    return result


def match_models(treatment, control):
    """One-to-one join by domain/sample/seed; absent pairs are accounted, not hidden.

    Values are metric scalars, not pixels. Caller must pass a predeclared roster
    to detect observations absent from *both* arms.
    """
    def index(records):
        result = {}
        for r in records:
            key = (r["domain"], r["sample_id"], r["seed"])
            if key in result:
                raise ValueError("duplicate model observation")
            result[key] = r
        return result
    left, right = index(treatment), index(control)
    rows = []
    for key in sorted(left.keys() & right.keys()):
        a, b = left[key], right[key]
        for field in ("patient_id", "population", "split", "metric_version", "threshold", "subgroup"):
            if a.get(field) != b.get(field):
                raise ValueError("paired provenance mismatch")
        if a.get("split") is not None and a["split"] not in {"TRAIN", "VAL", "SYNTHETIC"}:
            raise ValueError("prohibited paired split")
        rows.append({"domain": key[0], "sample_id": key[1], "seed": key[2],
                     **{k: a.get(k) for k in ("patient_id", "population", "split", "metric_version", "threshold", "subgroup")},
                     "treatment": a["value"], "control": b["value"]})
    return {"rows": rows, "n_matched": len(rows),
            "unmatched_treatment": [list(k) for k in sorted(left.keys() - right.keys())],
            "unmatched_control": [list(k) for k in sorted(right.keys() - left.keys())]}


def budget_quality(rows):
    """Descriptive measured cost/quality; equal budgets are not inferred."""
    out = []
    for r in rows:
        budget, quality = float(r["budget"]), float(r["quality"])
        if not np.isfinite(budget) or budget < 0 or not np.isfinite(quality):
            raise ValueError("finite nonnegative budget and finite quality required")
        out.append({"model": r["model"], "budget": budget, "budget_unit": r["budget_unit"],
                    "quality": quality, "quality_metric": r["quality_metric"]})
    return out


def equal_budget_comparison(treatment, control, *, budget_unit, atol=0.0):
    """Case-paired quality differences only at explicitly equal measured cost."""
    if not np.isfinite(atol) or atol < 0 or len(treatment) != len(control):
        raise ValueError("invalid budget tolerance or pairs")
    for a, b in zip(treatment, control):
        if a["sample_id"] != b["sample_id"] or a["budget_unit"] != budget_unit or b["budget_unit"] != budget_unit:
            raise ValueError("budget/sample identity mismatch")
        costs = np.asarray([a["budget"], b["budget"]], dtype=float)
        if not np.isfinite(costs).all() or np.any(costs < 0) or abs(costs[0] - costs[1]) > atol:
            raise ValueError("unequal/invalid budgets")
    return {"budget_unit": budget_unit, "equality_atol": atol, "quality": paired_summary(
        [r["quality"] for r in treatment], [r["quality"] for r in control]), "status": "DESCRIPTIVE_ONLY"}


def run_accounting(runs, *, arms, seeds):
    expected = {(a, s) for a in arms for s in seeds}
    seen, failed, incomplete = set(), [], []
    for r in runs:
        key = (r["arm"], r["seed"])
        if key not in expected or key in seen or r["status"] not in {"COMPLETE", "FAILED", "INCOMPLETE"}:
            raise ValueError("invalid/duplicate run identity or status")
        seen.add(key)
        if r["status"] == "FAILED":
            failed.append(list(key))
        if r["status"] != "COMPLETE":
            incomplete.append(list(key))
    missing = [list(k) for k in sorted(expected - seen)]
    return {"n_expected": len(expected), "n_recorded": len(seen), "missing_runs": missing,
            "failed_runs": failed, "incomplete_runs": incomplete,
            "primary_ready": not missing and not incomplete}


def subgroup_effects(rows, *, field="subgroup"):
    """Paired mean differences by recorded subgroup; absent metadata not invented."""
    result = []
    for group in sorted({str(r.get(field) or "NOT_AVAILABLE") for r in rows}):
        selected = [r for r in rows if str(r.get(field) or "NOT_AVAILABLE") == group]
        summary = paired_summary([r["treatment"] for r in selected], [r["control"] for r in selected])
        if group == "NOT_AVAILABLE":
            summary = {"n_total": len(selected), "n_missing_group_ids": len(selected), "mean": None}
        result.append({"group": group, "group_field": field,
                       "status": "NOT_AVAILABLE" if group == "NOT_AVAILABLE" else "DESCRIPTIVE_ONLY",
                       "summary": summary})
    return result


def c1_primary(rows, *, runs, expected_samples):
    """Frozen C1 mathematics; requires six complete matched runs.

    Input rows must be joined selected best_records. This function does not load
    or authenticate those records or a population roster and grants no execution.
    """
    accounting = run_accounting(runs, arms=("C1-T", "C1-C"), seeds=(42, 123, 3407))
    if not accounting["primary_ready"]:
        raise ValueError("C1 primary blocked: missing, failed or incomplete run")
    splits = {r.get("split") for r in rows}
    if len(splits) != 1 or not splits.issubset({"VAL", "SYNTHETIC"}):
        raise ValueError("C1 requires one VAL or synthetic population")
    roster = {}
    for r in expected_samples:
        key = (r["domain"], r["sample_id"])
        if key in roster or key[0] not in DOMAINS:
            raise ValueError("invalid C1 expected roster")
        roster[key] = r.get("patient_id")
    if splits == {"VAL"}:
        counts = {d: sum(dom == d for dom, _ in roster) for d in DOMAINS}
        if counts != {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}:
            raise ValueError("C1 VAL808 domain counts differ from frozen protocol")
    expected = {(d, sid, s) for d, sid in roster for s in (42, 123, 3407)}
    if not roster or {(r["domain"], r["sample_id"], r["seed"]) for r in rows} != expected:
        raise ValueError("C1 observed population differs from declared roster")
    for r in rows:
        if r.get("patient_id") != roster[(r["domain"], r["sample_id"])]:
            raise ValueError("C1 roster patient mismatch")
        if r.get("split") not in ("VAL", "SYNTHETIC") or r.get("metric_version") != "c1_phase21_compatibility_v1" or r.get("threshold") != 0.5:
            raise ValueError("C1 split/metric/threshold mismatch")
        if not 0 <= float(r["treatment"]) <= 1 or not 0 <= float(r["control"]) <= 1:
            raise ValueError("C1 invalid Dice")
    result = paired_bootstrap(rows, seeds=(42, 123, 3407), domains=DOMAINS,
                              n_boot=10000, rng_seed=20261027, confidence=0.95, patient_domains=("KUB",))
    result.update({"run_accounting": accounting, "evidence_class": "DEVELOPMENT_SELECTION_CONSUMED",
                   "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                   "multiplicity": "one primary; secondaries descriptive only", "seed_population_inference": False,
                   "n_declared_samples": len(roster), "claim_authorized": False,
                   "roster_authenticity": "caller-declared; must be independently audited against frozen population"})
    return result
