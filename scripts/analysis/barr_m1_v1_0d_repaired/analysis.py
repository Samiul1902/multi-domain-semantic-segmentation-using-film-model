"""Pure CPU array operations; no real-data runner is exposed in this release."""
import io
import re
from pathlib import Path
import numpy as np
import pandas as pd
from .contracts import (require, Refusal, digest, valid_sha, validate_config,
                        CONFIG, DOMAINS, COUNTS, SOURCES)


def checked_path(root, relative, allowed):
    root = Path(root).resolve()
    p = Path(relative)
    require(not p.is_absolute() and ".." not in p.parts, "E_PATH_UNAUTHORIZED")
    normalized = p.as_posix()
    require(normalized in allowed, "E_PATH_UNAUTHORIZED")
    require(not re.search(r"test|holdout|external|checkpoint|\.pt$", normalized, re.I), "E_PATH_PROTECTED")
    target = root / p
    for part in [target, *target.parents]:
        if part == root:
            break
        require(not part.is_symlink() and not getattr(part, "is_junction", lambda: False)(), "E_PATH_UNAUTHORIZED")
    require(target.resolve().is_relative_to(root), "E_PATH_UNAUTHORIZED")
    return target


def verified_csv(root, relative, expected, allowed):
    p = checked_path(root, relative, allowed)
    require(valid_sha(expected), "E_INPUT_SHA_MISSING")
    try:
        data = p.read_bytes()
    except OSError as exc:
        raise Refusal("E_INPUT_MISSING", str(exc)) from exc
    require(digest(data) == expected, "E_INPUT_SHA_MISMATCH")
    # Parse the exact verified bytes, eliminating hash/read TOCTOU.
    try:
        return pd.read_csv(io.BytesIO(data), dtype={"sample_id": str, "patient_id": str})
    except Exception as exc:
        raise Refusal("E_INPUT_SCHEMA", str(exc)) from exc


def load_production_sources(*args, **kwargs):
    # No callable bypass into real arrays in this engineering release.
    raise Refusal("E_EXECUTION_DISABLED")


def ids(frame, name):
    require("sample_id" in frame, "E_SAMPLE_ID_MISSING", name)
    s = frame.sample_id
    require(s.map(lambda x: isinstance(x, str) and bool(x.strip()) and x == x.strip()).all(),
            "E_SAMPLE_ID_MISSING", name)
    require(not s.duplicated().any(), "E_SAMPLE_ID_DUPLICATE", name)
    return set(s)


def columns(frame, names):
    require(set(names) <= set(frame.columns), "E_INPUT_SCHEMA", str(names))


def numeric(frame, name):
    columns(frame, [name])
    try:
        v = pd.to_numeric(frame[name], errors="raise").to_numpy(dtype=float)
    except (TypeError, ValueError):
        raise Refusal("E_INPUT_VALUE", name) from None
    require(np.isfinite(v).all(), "E_INPUT_VALUE", name)
    return v


def validate_population(frames, config=None):
    validate_config(CONFIG if config is None else config)
    require(set(frames) == set(SOURCES), "E_INPUT_SCHEMA", "exact input set required")
    lab, mem, saf, dev, grouping = [frames[k] for k in SOURCES]
    idsets = [ids(f, k) for k, f in frames.items()]
    require(all(len(s) == 4957 for s in idsets[:4]), "E_POPULATION_COUNT")
    require(all(s == idsets[0] for s in idsets[1:4]), "E_POPULATION_IDENTITY")
    require(idsets[0] <= idsets[4], "E_PATIENT_GROUP_MISSING")
    for f in (lab, saf, dev):
        columns(f, ["domain"])
        require(f.domain.notna().all() and f.domain.value_counts().to_dict() == COUNTS, "E_DOMAIN")
        require(f.set_index("sample_id").domain.sort_index().equals(
            dev.set_index("sample_id").domain.sort_index()), "E_DOMAIN_IDENTITY")
    columns(mem, ["selected", "budget", "lambda", "policy_id", "action_available"])
    require(mem.policy_id.eq("C8_lambda0.25_budget0.25").all(), "E_MEMBERSHIP_POLICY")
    require((numeric(mem, "budget") == .25).all() and (numeric(mem, "lambda") == .25).all(), "E_CONFIG_FROZEN")
    selected = numeric(mem, "selected")
    require(np.isin(selected, [0, 1]).all(), "E_MEMBERSHIP_VALUE")
    require(int(selected.sum()) == 1239, "E_A8_K")
    available = numeric(mem, "action_available")
    require(np.isin(available, [0, 1]).all() and (available[selected == 1] == 1).all(), "E_MEMBERSHIP_ELIGIBILITY")
    columns(lab, ["fold_refiner_checkpoint_sha", "action_available"])
    require(lab.fold_refiner_checkpoint_sha.map(valid_sha).all(), "E_CHECKPOINT_SHA_MISSING")
    require(lab.set_index("sample_id").action_available.sort_index().equals(
        mem.set_index("sample_id").action_available.sort_index()), "E_MEMBERSHIP_ELIGIBILITY")
    columns(grouping, ["patient_id", "split"])
    require(grouping.split.eq("train").all(), "E_POPULATION_PROTECTED")
    j = lab.merge(mem[["sample_id", "selected"]], on="sample_id", validate="one_to_one")
    columns(saf, ["safety_decision_oof", "p_accept_oof"])
    j = j.merge(saf[["sample_id", "p_accept_oof", "safety_decision_oof"]], on="sample_id", validate="one_to_one")
    j = j.merge(grouping[["sample_id", "patient_id"]], on="sample_id", validate="one_to_one")
    j = j.sort_values("sample_id", kind="stable").reset_index(drop=True)
    validate_grouping(j, expected_patients=267)
    d = numeric(j, "delta_dice")
    base, refined = numeric(j, "global_dice"), numeric(j, "candidate_refined_dice")
    require(((base >= 0) & (base <= 1) & (refined >= 0) & (refined <= 1)).all(), "E_DICE_RANGE")
    require(np.allclose(refined - base, d, rtol=0, atol=1e-9), "E_DELTA_INCONSISTENT")
    construct_deltas(j)
    return j


def construct_deltas(j):
    require(len(j) == 4957, "E_POPULATION_COUNT")
    sel = numeric(j, "selected")
    require(np.isin(sel, [0, 1]).all() and int(sel.sum()) == 1239, "E_A8_K")
    sel = sel.astype(bool)
    p = numeric(j, "p_accept_oof")
    columns(j, ["safety_decision_oof"])
    require(j.safety_decision_oof.isin(["ACCEPT_REFINEMENT", "FALLBACK_GLOBAL"]).all(), "E_SAFETY_VALUE")
    dec = j.safety_decision_oof.eq("ACCEPT_REFINEMENT").to_numpy()
    require(((p >= 0) & (p <= 1)).all(), "E_SAFETY_VALUE")
    # Consume frozen binary decision; probability comparison is consistency-only.
    require(np.array_equal(dec.astype(bool), p >= .5), "E_SAFETY_INCONSISTENT")
    acc = sel & dec.astype(bool)
    require(int(acc.sum()) == 1205 and int((sel & ~acc).sum()) == 34, "E_A8_PARTITION")
    d = numeric(j, "delta_dice")
    arms = {"A0": np.zeros(len(j)), "A1": d.copy(), "A8": np.where(acc, d, 0.)}
    validate_deltas(arms, j, sel, acc)
    return arms, sel, acc


def validate_deltas(arms, j, sel, acc):
    require(set(arms) == {"A0", "A1", "A8"}, "E_ARM_SCOPE")
    require(all(np.asarray(v).shape == (len(j),) and np.isfinite(v).all() for v in arms.values()), "E_DELTA_INVALID")
    require((arms["A0"] == 0).all() and (arms["A8"][~acc] == 0).all(), "E_STRUCTURAL_ZERO")
    require(np.array_equal(arms["A1"], j.delta_dice.to_numpy()) and
            np.array_equal(arms["A8"][acc], arms["A1"][acc]), "E_DELTA_INCONSISTENT")


def validate_grouping(j, expected_patients=None):
    columns(j, ["domain", "patient_id", "sample_id"])
    ids(j, "grouping")
    require(set(j.domain) == set(DOMAINS), "E_DOMAIN")
    kub = j.loc[j.domain == "KUB", "patient_id"]
    require(kub.map(lambda x: isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9_.:-]+", x) is not None
                    and x.upper() not in {"NOT_AVAILABLE", "NAN", "NONE", "NULL"}).all(), "E_KUB_PATIENT_ID")
    if expected_patients is not None:
        require(kub.nunique() == expected_patients, "E_KUB_PATIENT_COUNT")
    require(j.loc[j.domain != "KUB", "patient_id"].eq("NOT_AVAILABLE").all(), "E_GROUPING_CONTRACT")


def resampling_plan(j):
    validate_grouping(j)
    plan = {}
    for domain in DOMAINS:
        ix = np.flatnonzero(j.domain.to_numpy() == domain)
        if domain == "KUB":
            patients = j.patient_id.to_numpy()[ix]
            plan[domain] = [ix[patients == p] for p in sorted(set(patients))]
        else:
            plan[domain] = ix
    return plan


def draw_plan(plan, rng):
    out = {}
    for domain, units in plan.items():
        if domain == "KUB":
            out[domain] = np.concatenate([units[k] for k in rng.choice(len(units), len(units), replace=True)])
        else:
            out[domain] = rng.choice(units, len(units), replace=True)
    return out


def resample_indices(j, rng):
    out = draw_plan(resampling_plan(j), rng)
    validate_resample(j, out)
    return out


def validate_resample(j, sample):
    require(set(sample) == set(DOMAINS), "E_RESAMPLE_DOMAIN")
    for domain in DOMAINS:
        ix = np.asarray(sample[domain])
        require(ix.ndim == 1 and len(ix) > 0 and np.issubdtype(ix.dtype, np.integer)
                and ((ix >= 0) & (ix < len(j))).all(), "E_RESAMPLE_INDEX")
        require(j.iloc[ix].domain.eq(domain).all(), "E_RESAMPLE_DOMAIN")
        original = np.flatnonzero(j.domain.to_numpy() == domain)
        if domain != "KUB":
            require(len(ix) == len(original), "E_RESAMPLE_SIZE")
        else:
            counts = np.bincount(ix, minlength=len(j))
            patients = j.patient_id.to_numpy()
            multiplicities = []
            for patient in sorted(set(patients[original])):
                case_counts = counts[original[patients[original] == patient]]
                require((case_counts == case_counts[0]).all(), "E_KUB_CLUSTER_SPLIT")
                multiplicities.append(int(case_counts[0]))
            require(sum(multiplicities) == len(multiplicities), "E_KUB_CLUSTER_COUNT")


def macro_mean(values, domains):
    require(set(domains) == set(DOMAINS), "E_DOMAIN")
    return float(np.mean([np.mean(values[np.asarray(domains) == d]) for d in DOMAINS]))


def validate_macro(reported, values, domains):
    require(abs(reported - macro_mean(values, domains)) <= 1e-12, "E_MACRO_ESTIMAND")


def harm(values, executed):
    n = len(values)
    return {name: dict(count=int((values < threshold).sum()),
                      rate_all=float((values < threshold).sum() / n),
                      rate_conditional=float((values < threshold).sum() / executed) if executed else None)
            for name, threshold in (("strict", 0), ("tolerance_adjusted", -1e-9))}


def statistics(arms, j):
    expected, sel, acc = construct_deltas(j)
    validate_deltas(arms, j, sel, acc)
    output = {}
    for arm, values in arms.items():
        selected = np.zeros(len(j), bool) if arm == "A0" else np.ones(len(j), bool) if arm == "A1" else sel
        accepted = acc if arm == "A8" else selected
        # Refiner execution precedes post-safety: A8 executes 1239 candidates,
        # but applies only 1205. Never derive these counts from nonzero deltas.
        row = dict(n_candidate_executed=int(selected.sum()), n_selected=int(selected.sum()),
                   n_accepted=int(accepted.sum()), n_rejected=int((selected & ~accepted).sum()))
        row.update(macro_delta=macro_mean(values, j.domain.to_numpy()),
                   pooled_delta_all=float(values.mean()),
                   pooled_delta_applied=float(values.sum()/accepted.sum()) if accepted.any() else None,
                   harm=harm(values, int(accepted.sum())))
        row["per_domain"] = {d: dict(n=int((j.domain == d).sum()),
            delta_mean=float(values[j.domain == d].mean()),
            dice_mean=float((j.global_dice.to_numpy() + values)[j.domain == d].mean()),
            harm=harm(values[j.domain == d], int(accepted[j.domain == d].sum()))) for d in DOMAINS}
        row["macro_dice"] = float(np.mean([v["dice_mean"] for v in row["per_domain"].values()]))
        output[arm] = row
    return output


def bootstrap(arms, j, config=None):
    validate_config(CONFIG if config is None else config)
    validate_grouping(j)
    require(set(arms) == {"A0", "A1", "A8"}, "E_ARM_SCOPE")
    require(all(np.asarray(v).shape == (len(j),) and np.isfinite(v).all() for v in arms.values()), "E_DELTA_INVALID")
    # Canonical ID ordering makes row permutations irrelevant to seeded results.
    order = np.argsort(j.sample_id.to_numpy(), kind="stable")
    j = j.iloc[order].reset_index(drop=True)
    contrasts = [("A8-A0", "A8", "A0"), ("A8-A1", "A8", "A1"), ("A1-A0", "A1", "A0")]
    diffs = np.column_stack([(arms[a] - arms[b])[order] for _, a, b in contrasts])
    rng = np.random.default_rng(42)
    plan = resampling_plan(j)
    draws = np.empty((2000, 3))
    for r in range(2000):
        sample = draw_plan(plan, rng)
        draws[r] = np.mean([diffs[sample[d]].mean(axis=0) for d in DOMAINS], axis=0)
    return {name: dict(observed_macro=macro_mean(diffs[:, c], j.domain.to_numpy()),
            observed_pooled_all=float(diffs[:, c].mean()),
            macro_ci95=np.quantile(draws[:, c], [.025, .975]).tolist(),
            replicates=2000, seed=42, grouping_limitation="ISIC/BUSI/KVASIR: patient IDs NOT_AVAILABLE; per-case resampling")
            for c, (name, _, _) in enumerate(contrasts)}


def analyze_frames(frames, config=None):
    """Pure computation kernel for tests and a future separately approved runner.

    No file loading or production authorization is provided by this function.
    """
    validate_config(CONFIG if config is None else config)
    j = validate_population(frames, config)
    arms, selected, accepted = construct_deltas(j)
    per_case = []
    for i, row in j.iterrows():
        per_case.append(dict(sample_id=row.sample_id, domain=row.domain, patient_id=row.patient_id,
            selected=bool(selected[i]), accepted=bool(accepted[i]), rejected=bool(selected[i] and not accepted[i]),
            skipped=bool(not selected[i]), **{arm+"_delta": float(v[i]) for arm, v in arms.items()}))
    return dict(study="BARR-M1", classification="DESCRIPTIVE_POLICY_COMPARISON",
                population="ROUTER_DEVELOPMENT", n=4957, evaluation="IN_SAMPLE",
                per_case=per_case, arm_and_domain_statistics=statistics(arms, j),
                paired_contrasts=bootstrap(arms, j, config))
