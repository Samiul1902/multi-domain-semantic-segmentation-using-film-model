"""Focused tests for the external-evidence reconciliation.

These tests bind the report and the figures to the frozen artifacts, so that a
future edit which reintroduces an unsupported number fails CI instead of
silently shipping.

They do not train, do not infer, and do not touch TEST / ROUTER_HOLDOUT.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports/audits/c1_external_evidence_v1_0"
PROV = AUDIT / "claim_provenance.json"
DOCX = ROOT / "paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx"
MS = ROOT / "docs/manuscript/RA_MEDFILM_BARR_MANUSCRIPT_DRAFT.md"


# --------------------------------------------------------------- helpers
def docx_text():
    """Return (paragraph_text, list_of_table_texts)."""
    import docx
    d = docx.Document(str(DOCX))
    paras = [p.text for p in d.paragraphs]
    tables = []
    for t in d.tables:
        cells = []
        for r in t.rows:
            for c in r.cells:
                cells.append(c.text)
        tables.append("\n".join(cells))
    return "\n".join(paras), tables


def docx_all():
    """Paragraphs and tables combined, for 'does the report contain this value' checks."""
    paras, tables = docx_text()
    return paras + "\n" + "\n".join(tables)


def docx_table_headers():
    import docx
    d = docx.Document(str(DOCX))
    return [" | ".join(c.text for c in t.rows[0].cells) for t in d.tables]


# ------------------------------------------------------- provenance record
def test_provenance_record_exists_and_is_valid():
    assert PROV.is_file(), "claim_provenance.json missing"
    rec = json.loads(PROV.read_text(encoding="utf-8"))
    assert rec["schema"] == "c1_external_evidence_provenance_v1_0"
    assert rec["scientific_execution"] is False
    assert rec["training_performed"] is False
    assert rec["test_or_router_holdout_accessed"] is False
    assert len(rec["entries"]) >= 15


def test_every_provenance_entry_has_a_verdict_and_an_existing_source():
    rec = json.loads(PROV.read_text(encoding="utf-8"))
    allowed = {"VERIFIED", "PARTIALLY_VERIFIED", "UNSUPPORTED", "MISATTRIBUTED"}
    for e in rec["entries"]:
        assert e["verdict"] in allowed, e["claim_id"]
        assert e["source_exists"], f"{e['claim_id']} source missing: {e['source_artifact']}"


def test_file_sources_still_match_their_recorded_sha256():
    """A drifted artifact must fail here rather than silently change the report."""
    rec = json.loads(PROV.read_text(encoding="utf-8"))
    drifted = []
    for e in rec["entries"]:
        if e["source_kind"] != "file" or not e["source_sha256"]:
            continue
        p = ROOT / e["source_artifact"]
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() != e["source_sha256"]:
            drifted.append(e["claim_id"])
    assert not drifted, f"sources drifted since the audit: {drifted}"


# ------------------------------------------------------- internal values
def test_global_film_val808_macro_dice_matches_phase21_record():
    rec = json.loads(PROV.read_text(encoding="utf-8"))
    e = {x["claim_id"]: x for x in rec["entries"]}["INT-01"]
    p21 = json.loads((ROOT / "reports/audits/phase21_analysis.json").read_text(encoding="utf-8"))
    assert abs(e["value"] - p21["global_medfilm"]["macro_domain_dice"] * 100) < 1e-3
    assert abs(e["value"] - 83.5079) < 1e-3


def test_six_model_table_matches_phase21_csv_exactly():
    rows = list(csv.DictReader(open(ROOT / "reports/tables/phase21_six_model_comparison.csv",
                                    encoding="utf-8-sig")))
    expected = {r["model_key"]: round(float(r["macro_domain_dice"]) * 100, 2) for r in rows}
    assert expected["global_medfilm"] == 83.51
    assert expected["deeplabv3plus"] == 82.77
    assert expected["unet"] == 78.78

    body = docx_all()
    for label in ("83.51%", "82.77%", "82.24%", "79.20%", "78.90%", "78.78%"):
        assert label in body, f"verified baseline value {label} missing from report"


def test_barr_val808_value_is_the_phase29_three_seed_mean_not_86_24():
    g = json.loads((ROOT / "reports/audits/phase21_analysis.json").read_text(encoding="utf-8"))
    p29 = json.loads((ROOT / "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json")
                     .read_text(encoding="utf-8"))
    barr = (g["global_medfilm"]["macro_domain_dice"] + p29["macro_delta_dice"]["mean"]) * 100
    assert abs(barr - 83.7902) < 1e-3
    assert abs(barr - 86.24) > 1.0, "the retracted 86.24 value must not be reproducible"


def test_barr_parameter_total_is_verified_component_sum():
    p36 = json.loads((ROOT / "reports/audits/phase36_robustness_scientific_result_v1_23.json")
                     .read_text(encoding="utf-8"))
    comps = p36["component_load_audit"]["components"]
    total = sum(c["parameter_count"] for c in comps.values())
    assert total == 4837420
    assert total != 4800000
    assert "4,837,420" in docx_all()


def test_holdout_values_match_phase30():
    p30 = json.loads((ROOT / "reports/audits/phase30_primary_noninferiority_result.json")
                     .read_text(encoding="utf-8"))
    assert round(p30["global_macro_dice"] * 100, 2) == 92.85
    assert round(p30["a8_macro_dice"] * 100, 2) == 93.03
    assert p30["p_values_computed"] == 0
    body = docx_all()
    assert "92.85%" in body and "93.03%" in body


def test_harm_attribution_is_decomposed_correctly():
    rows = {r["arm"]: r for r in csv.DictReader(
        open(ROOT / "reports/tables/phase28_table_02_arm_primary_metrics.csv", encoding="utf-8-sig"))}
    a1 = int(rows["A1"]["n_harmful_routed"])
    a7 = int(rows["A7"]["n_harmful_routed"])
    a8 = int(rows["A8"]["n_harmful_routed"])
    assert (a1, a7, a8) == (2115, 412, 390)
    assert a1 - a8 == 1725          # system-level
    assert a1 - a7 == 1703          # router
    assert a7 - a8 == 22            # safety filter alone
    body = docx_all()
    assert "1,703" in body and "22 cases" in body


# ------------------------------------------------------- retractions
RETRACTION_HEADER = "Statement in the previous build"


def test_retracted_86_24_appears_only_in_the_retraction_register():
    paras, tables = docx_text()
    assert "86.24" not in paras, "86.24 must not appear in report prose"
    hits = [t for t in tables if "86.24" in t]
    assert len(hits) == 1, "86.24 should appear exactly once, in the retraction table"
    assert RETRACTION_HEADER in hits[0]


def test_no_fabricated_p_values_in_report_prose():
    paras, tables = docx_text()
    for needle in ("p<0.001", "p<0.01", "(Significant)"):
        assert needle not in paras, f"fabricated statistic {needle} in prose"
        hits = [t for t in tables if needle in t]
        for h in hits:
            assert RETRACTION_HEADER in h, f"{needle} used outside the retraction register"


def test_retracted_tiny_stratum_claim_is_not_asserted():
    paras, _ = docx_text()
    assert "85.57%" not in paras or "retracted" in paras.lower()
    # the legitimate holdout KUB value may remain in a table
    _, tables = docx_text()
    holdout = [t for t in tables if "84.97%" in t]
    assert holdout, "holdout KUB row missing"
    assert "85.57%" in holdout[0]


def test_report_states_that_barr_was_not_executed_externally():
    body, _ = docx_text()
    assert "BARR components were not loaded" in body or "no BARR decision" in body.lower()
    assert "Triggered" not in body


# ------------------------------------------------------- figures
@pytest.mark.parametrize("name", [
    "fig1_model_comparison.png",
    "fig2_domain_performance.png",
    "fig3_safety_compute.png",
    "fig4_internal_4domain_predictions.png",
    "fig5_external_4domain_predictions.png",
])
def test_figure_exists_and_is_non_trivial(name):
    p = ROOT / "paper_doc" / name
    assert p.is_file(), f"{name} missing"
    assert p.stat().st_size > 50_000, f"{name} suspiciously small"


def test_every_figure_has_a_generating_script():
    assert (ROOT / "scripts/analysis/build_verified_comparison_figures.py").is_file()
    assert (ROOT / "scripts/analysis/generate_prediction_panels.py").is_file()


def test_panel_generator_no_longer_asserts_a_barr_action():
    src = (ROOT / "scripts/analysis/generate_prediction_panels.py").read_text(encoding="utf-8")
    assert "Triggered" not in src
    assert "S_omega Triggered" not in src
    # it must still record that only the global model runs
    assert "Global FiLM only" in src or "BARR not loaded" in src or "no BARR component" in src


def test_panel_generator_uses_the_required_error_colours():
    src = (ROOT / "scripts/analysis/generate_prediction_panels.py").read_text(encoding="utf-8")
    for rgb in ("(0, 230, 0)", "(255, 32, 32)", "(32, 96, 255)", "(24, 24, 24)"):
        assert rgb in src, f"required TP/FP/FN/TN colour {rgb} missing"


def test_figure_generator_binds_to_authoritative_artifacts_only():
    src = (ROOT / "scripts/analysis/build_verified_comparison_figures.py").read_text(encoding="utf-8")
    assert "phase21_six_model_comparison.csv" in src
    assert "phase29_phase_d_three_seed_descriptive_summary.json" in src
    assert "phase30_primary_noninferiority_result.json" in src
    assert "phase28_table_02_arm_primary_metrics.csv" in src
    # must not contain the retracted value
    assert "86.24" not in src


# ------------------------------------------------------- manuscript
def test_manuscript_has_no_retracted_superiority_or_compute_claims():
    t = MS.read_text(encoding="utf-8")
    assert "86.24" not in t
    assert "4.2 \\text{ GFLOPs}" not in t
    assert "IRB provenance" not in t
    assert "immune to post-hoc cherry-picking" not in t
    assert "superior multi-domain stability" not in t


def test_manuscript_contains_the_external_pilot_with_qualification():
    t = MS.read_text(encoding="utf-8")
    assert "13.1 External pilot" in t
    assert "PARTIALLY_VERIFIED" in t
    assert "not an external validation cohort" in t
    assert "undocumented source" in t


def test_manuscript_states_preservation_not_improvement():
    t = MS.read_text(encoding="utf-8")
    assert "preserves" in t.lower()
    assert "+0.17 pp" in t
    assert "no p-value" in t.lower() or "no confirmatory" in t.lower()


def test_manuscript_parameter_total_present():
    t = MS.read_text(encoding="utf-8")
    assert "4,837,420" in t
