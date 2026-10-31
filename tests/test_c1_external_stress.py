"""Tests for the external stress-test artefacts.

These bind the plan, the result arrays, the tables and the documents to each
other, so that a future edit which silently changes a number, drops a cohort,
reintroduces a millimetre surface metric or weakens the retrospective framing
fails CI instead of shipping.

They do not train, do not infer, and do not touch TEST / ROUTER_HOLDOUT.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "reports/audits/c1_external_stress_v1_0"
TAB = ROOT / "reports/tables"
CACHE = ROOT / "data_cache/c1_external_stress_v1_0"
DOCX = ROOT / "paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx"
MS = ROOT / "docs/manuscript/RA_MEDFILM_BARR_MANUSCRIPT_DRAFT.md"

COHORTS = {"cvc": 612, "breast": 252, "stones": 20}


# --------------------------------------------------------------- helpers
def load(name):
    return json.loads((AUD / name).read_text(encoding="utf-8"))


def sha256_file(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def docx_text():
    import docx
    d = docx.Document(str(DOCX))
    paras = [p.text for p in d.paragraphs]
    tables = []
    for t in d.tables:
        cells = [c.text for r in t.rows for c in r.cells]
        tables.append("\n".join(cells))
    return "\n".join(paras), tables


def docx_all():
    paras, tables = docx_text()
    return paras + "\n" + "\n".join(tables)


# --------------------------------------------------------------- plan
def test_plan_documents_exist_and_match_their_manifest():
    man = load("plan_manifest.json")
    assert man["self_digest_included"] is False
    for name, digest in man["documents"].items():
        p = AUD / name
        assert p.is_file(), f"missing plan document {name}"
        assert sha256_file(p) == digest, f"{name} changed after the plan was frozen"


def test_every_bound_input_still_matches_the_plan():
    man = load("plan_manifest.json")
    drift = {}
    for key, rec in man["bound_inputs"].items():
        p = ROOT / rec["path"]
        if not p.is_file():
            drift[key] = "missing"
        elif sha256_file(p) != rec["sha256"]:
            drift[key] = "sha256 changed"
    assert not drift, f"bound input drift: {drift}"


def test_plan_is_pre_registered_and_retrospective():
    plan = load("external_stress_plan.json")
    assert plan["classification"] == "RETROSPECTIVE_EXTERNAL_STRESS_TEST"
    assert plan["statistics"]["p_values_computed"] == 0
    assert plan["metrics"]["cross_cohort_pooling"] is False
    assert plan["metrics"]["surface_units"] == "pixels"
    assert "before any external probability array" in plan["clock_caveat"]


# --------------------------------------------------------------- cohorts
def test_cohort_sizes_are_exactly_the_frozen_ones():
    cc = load("cohort_construction.json")
    for key, n in COHORTS.items():
        assert cc["cohorts"][key]["rows_analysed"] == n, key
    assert cc["total_analysed"] == 884


def test_ham10000_is_excluded_and_has_zero_rows():
    cc = load("cohort_construction.json")
    ham = cc["cohorts"]["ham10000"]
    assert ham["rows_analysed"] == 0
    assert ham["status"] == "HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED"
    assert not (CACHE / "ham10000").exists()


def test_no_cohort_was_dropped_post_hoc():
    cc = load("cohort_construction.json")
    for key in COHORTS:
        assert cc["cohorts"][key]["n_post_hoc_drops"] == 0


def test_sample_id_lists_match_their_recorded_digest():
    cc = load("cohort_construction.json")
    for key in COHORTS:
        ids = json.loads((CACHE / key / "sample_ids.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()
        assert digest == cc["cohorts"][key]["sample_ids_sha256"], key
        assert len(ids) == COHORTS[key]


# --------------------------------------------------------------- arrays
@pytest.mark.parametrize("key", list(COHORTS))
def test_saved_arrays_are_consistent(key):
    n = COHORTS[key]
    pg = np.load(CACHE / key / "prob_global.npy")
    pred = np.load(CACHE / key / "pred_global.npy")
    gt = np.load(CACHE / key / "gt.npy")
    assert pg.shape == (n, 512, 512)
    assert pg.dtype == np.float32
    assert pred.shape == gt.shape == (n, 512, 512)
    assert pred.dtype == np.uint8 and gt.dtype == np.uint8
    # probability is a probability
    assert float(pg.min()) >= 0.0 and float(pg.max()) <= 1.0
    # the saved binary mask IS the thresholded probability, not a re-derivation
    assert np.array_equal(pred.astype(bool), pg >= np.float32(0.5))
    # ground truth is binary
    assert set(np.unique(gt).tolist()) <= {0, 1}


@pytest.mark.parametrize("key", list(COHORTS))
def test_barr_arrays_are_consistent(key):
    n = COHORTS[key]
    pb = np.load(CACHE / key / "prob_barr.npy")
    pred = np.load(CACHE / key / "pred_barr.npy")
    assert pb.shape == (n, 512, 512) and pb.dtype == np.float32
    assert np.array_equal(pred.astype(bool), pb >= np.float32(0.5))


@pytest.mark.parametrize("key", list(COHORTS))
def test_unselected_cases_keep_the_global_mask_exactly(key):
    """A case the router skipped, or the safety gate rejected, must be bit-identical."""
    states = pd.read_csv(CACHE / key / "barr_states.csv")
    pg = np.load(CACHE / key / "prob_global.npy")
    pb = np.load(CACHE / key / "prob_barr.npy")
    keep = states["state"].isin(["NOT_ATTEMPTED", "REJECTED", "FAILED"])
    if keep.any():
        idx = np.flatnonzero(keep.to_numpy())
        assert np.array_equal(pg[idx], pb[idx]), "a skipped/rejected case was modified"


# --------------------------------------------------------------- BARR states
@pytest.mark.parametrize("key", list(COHORTS))
def test_barr_states_partition_every_case(key):
    ex = load("barr_executability.json")
    st = ex["observed_states"][key]
    assert sum(st.values()) == COHORTS[key], f"{key} states do not sum to n"
    allowed = {"NOT_ATTEMPTED", "ROUTED", "EXECUTED", "ACCEPTED",
               "REJECTED", "FALLBACK_TO_GLOBAL", "FAILED"}
    assert set(st) <= allowed


def test_barr_had_no_failures_and_no_roi_fallbacks():
    ex = load("barr_executability.json")
    assert ex["n_failed"] == 0
    assert ex["n_fallback_to_global"] == 0
    assert ex["evidence"]["n_cases_where_decision_forms_disagreed"] == 0


def test_barr_was_executable_not_declared_unexecutable():
    ex = load("barr_executability.json")
    assert ex["determination"] == "BARR_EXECUTABLE_FROM_VERIFIED_ARTIFACTS"
    assert ex["evidence"]["components_hash_verified_before_forward"] is True
    assert ex["evidence"]["strict_state_dict_loading"] is True
    assert ex["evidence"]["component_parameter_counts"]["total"] == 4837420


def test_selection_fraction_is_reported_as_an_outcome():
    ex = load("barr_executability.json")
    for key in COHORTS:
        assert 0.0 <= ex["selection_fraction"][key] <= 1.0
    assert "OUTCOME" in ex["caveat"]


# --------------------------------------------------------------- metrics
def test_metrics_declare_no_confirmatory_p_values():
    m = load("metrics_summary.json")
    assert m["p_values_computed"] == 0
    assert m["surface_units"] == "pixels"
    assert m["cross_cohort_pooling"] is False


def test_per_case_metrics_recompute_from_the_arrays():
    """Spot-check the arithmetic on the first case of each cohort."""
    pc = pd.read_csv(TAB / "c1_external_stress_per_case.csv")
    for key in COHORTS:
        for arm in ("global", "barr"):
            row = pc[(pc.cohort_key == key) & (pc.arm == arm)].iloc[0]
            pg = np.load(CACHE / key / f"prob_{arm}.npy")
            gt = np.load(CACHE / key / "gt.npy").astype(bool)
            pred = pg[row["index"]] >= np.float32(0.5)
            g = gt[row["index"]]
            tp = int((pred & g).sum())
            fp = int((pred & ~g).sum())
            fn = int((~pred & g).sum())
            assert (tp, fp, fn) == (row["TP"], row["FP"], row["FN"])
            if 2 * tp + fp + fn:
                assert abs(row["Dice"] - 2 * tp / (2 * tp + fp + fn)) < 1e-12


def test_summary_means_match_the_per_case_table():
    pc = pd.read_csv(TAB / "c1_external_stress_per_case.csv")
    summ = pd.read_csv(TAB / "c1_external_stress_summary.csv")
    for key in COHORTS:
        for arm in ("global", "barr"):
            got = summ[(summ.cohort_key == key) & (summ.arm == arm)
                       & (summ.metric == "Dice")].iloc[0]["mean"]
            want = pc[(pc.cohort_key == key) & (pc.arm == arm)]["Dice"].mean()
            assert abs(got - want) < 1e-12


def test_domain_shift_is_external_minus_internal():
    ds = pd.read_csv(TAB / "c1_external_stress_domain_shift.csv")
    for _, r in ds.iterrows():
        assert abs((r["external_global_dice"] - r["internal_val808_dice"]) * 100
                   - r["delta_vs_internal_pp"]) < 1e-6


def test_stones_is_reported_as_three_statements():
    sub = pd.read_csv(TAB / "c1_external_stress_stones_subgroups.csv")
    assert set(sub["subgroup"]) == {"six_positive", "fourteen_absent"}
    assert set(sub[sub.subgroup == "six_positive"]["n"]) == {6}
    assert set(sub[sub.subgroup == "fourteen_absent"]["n"]) == {14}


def test_all_fourteen_stone_free_images_are_false_positives():
    pc = pd.read_csv(TAB / "c1_external_stress_per_case.csv")
    st = pc[(pc.cohort_key == "stones") & (pc.arm == "global")]
    absent = st[st.gt_pixels == 0]
    assert len(absent) == 14
    assert bool(absent["fp_only_case"].all()), "a stone-free image produced no foreground"


def test_surface_metrics_are_undefined_not_zero_where_gt_is_empty():
    pc = pd.read_csv(TAB / "c1_external_stress_per_case.csv")
    st = pc[(pc.cohort_key == "stones") & (pc.arm == "global") & (pc.gt_pixels == 0)]
    assert st["HD95_px"].isna().all(), "surface distance was fabricated for an empty GT"


# --------------------------------------------------------------- documents
def test_report_contains_the_actual_external_numbers():
    text = docx_all()
    for token in ("68.66%", "70.78%", "8.08%", "26.95%", "884", "14 of 14"):
        assert token in text, f"report is missing {token}"


def test_report_no_longer_contains_the_retracted_pilot_values():
    paras, tables = docx_text()
    everything = "\n".join(tables)
    # the retraction register legitimately names 79.15%; the prose must not quote it as a result
    assert "79.15" not in paras
    # the withdrawn pilot's per-case numbers must be gone from the tables too
    for dead in ("42.69%", "18.86%", "5.65%", "88.17%"):
        assert dead not in everything, f"retracted pilot value {dead} still in a table"


def test_report_states_the_retrospective_classification():
    text = docx_all()
    assert "RETROSPECTIVE_EXTERNAL_STRESS_TEST" in text


def test_report_declares_pixels_for_surface_metrics():
    text = docx_all()
    assert "PIXELS" in text.upper()
    assert "millimetre" in text.lower()


def test_manuscript_no_longer_describes_a_four_case_pilot_as_the_external_result():
    md = MS.read_text(encoding="utf-8")
    assert "retrospective external stress test on 884 cases" in md
    assert "| HAM10000 (ISIC-2018 Task 3)" not in md, "the retracted pilot table is still present"
    assert "### 13.1 External stress test" in md
    # the withdrawn pilot is named exactly once, as withdrawn
    assert md.count("withdrawn in full") == 1


def test_manuscript_declares_pixel_units_and_no_validation():
    md = MS.read_text(encoding="utf-8")
    assert "ships pixel spacing" in md
    assert "external validation has **not** been performed" in md


def test_no_millimetre_surface_number_appears_in_the_external_audit():
    """Guards against a mm measurement being pasted into an external artefact.

    Only a numeric millimetre value counts; the bare substring 'mm' occurs inside
    ordinary words (summary, comment) and inside SHA-256 digests.
    """
    import re
    pattern = re.compile(r"\d+(?:\.\d+)?\s*mm\b", re.IGNORECASE)
    # narrative files quote the protocol's 1.0 mm target in order to explain why it was
    # not used; only result-bearing files must be free of millimetre measurements
    narrative = {"deviations.json", "plan_manifest.json", "external_stress_plan.json"}
    checked = 0
    for p in AUD.glob("*.json"):
        if p.name in narrative:
            continue
        checked += 1
        txt = p.read_text(encoding="utf-8")
        assert not pattern.search(txt), f"{p.name} contains a millimetre measurement"
    assert checked >= 5, "the check did not actually run over the result files"


# --------------------------------------------------------------- figures
def test_figures_exist_and_are_non_trivial():
    for name in ("fig6_external_cvc.png", "fig7_external_breast.png",
                 "fig8_external_stones.png"):
        p = ROOT / "reports/figures" / name
        assert p.is_file(), name
        assert p.stat().st_size > 200_000, f"{name} looks empty"


def test_figure_generator_uses_the_required_error_palette():
    src = (ROOT / "scripts/analysis/build_external_stress_figures.py").read_text(encoding="utf-8")
    for rgb in ("(0, 230, 0)", "(255, 32, 32)", "(32, 96, 255)", "(24, 24, 24)"):
        assert rgb in src, f"error colour {rgb} missing from the figure generator"


def test_figure_manifest_records_eight_columns():
    man = load("figures_manifest.json")
    assert man["columns"] == 8
    assert len(man["figures"]) == 3


# --------------------------------------------------------------- governance
def test_deviations_are_declared_with_a_reason():
    d = load("deviations.json")
    assert d["n_deviations"] == len(d["deviations"])
    for dev in d["deviations"]:
        assert dev["reason"], dev["id"]
        assert dev["effect_on_results"], dev["id"]


def test_c1_trust_boundary_is_still_closed():
    """This study must not have opened the C1 gate."""
    plan = load("external_stress_plan.json")
    assert plan["c1_status"]["decision"] == "NO-GO"
    assert plan["c1_status"]["scientific_execution_enabled"] is False
    assert plan["c1_status"]["approval"] is False
