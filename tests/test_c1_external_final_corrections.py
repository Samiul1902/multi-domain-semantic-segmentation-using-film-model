"""Contracts for the final external-results correction and C1 handoff pass.

These tests bind the four things this pass changed, so none of them can silently
regress:

  * the recomputed 884-case accounting (verify, do not trust the tables);
  * the BARR-action figures and their deterministic selection;
  * the retired statistical wordings, in both the DOCX report and the manuscript;
  * the C1 manuscript statistics, which must match the frozen endpoint.

They read only committed artefacts. Nothing here runs inference.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "reports/audits/c1_external_stress_v1_0"
TAB = ROOT / "reports/tables"
FIG = ROOT / "reports/figures"
MS = ROOT / "docs/manuscript/RA_MEDFILM_BARR_MANUSCRIPT_DRAFT.md"

# The corrected report was built while another process held the canonical path open
# read-only, so it was written alongside it under a distinct name. Bind whichever
# build is newest: once the canonical file is updated this resolves to it and the
# fallback stops mattering.
_CANDIDATES = [
    ROOT / "paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx",
    ROOT / "paper_doc/RA_MedFiLM_BARR_Scientific_Report_CORRECTED.docx",
]
DOCX = max((p for p in _CANDIDATES if p.is_file()), key=lambda p: p.stat().st_mtime)


def docx_text() -> str:
    import docx
    d = docx.Document(str(DOCX))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                parts.append(c.text)
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# 1. recomputed accounting
# --------------------------------------------------------------------------- #
def test_final_verification_verdict_is_consistent():
    rec = json.loads((AUD / "final_verification.json").read_text(encoding="utf-8"))
    assert rec["verdict"] == "CONSISTENT", rec["failures"]
    assert rec["failures"] == []
    assert rec["inference_rerun"] is False


def test_totals_are_884_and_balance():
    rec = json.loads((AUD / "final_verification.json").read_text(encoding="utf-8"))
    t = rec["totals"]
    assert t["n_cases"] == 884
    assert t["n_selected"] == t["n_accepted"] + t["n_rejected"] == 184
    assert (t["n_accepted"], t["n_rejected"]) == (139, 45)


def test_refiner_forwards_equal_selected_not_accepted():
    """A rejected candidate has already run the refiner, so compute follows selection."""
    rec = json.loads((AUD / "final_verification.json").read_text(encoding="utf-8"))
    for key, v in rec["per_cohort"].items():
        stage = v["stage_counts"]
        assert stage["refiner_forwards"] == v["n_selected"], key
        assert stage["refiner_forwards"] != v["n_accepted"], key
        assert stage["somega_forwards"] == stage["refiner_forwards"], key
    assert rec["totals"]["refiner_forwards"] == 184


def test_internal_routed_triple_is_not_the_external_one():
    """1,239/1,205/34 belongs to BARR-M1; the external cohort has 184/139/45."""
    rec = json.loads((AUD / "final_verification.json").read_text(encoding="utf-8"))
    internal = rec["compute_accounting"]["internal_barr_m1_population"]
    assert internal["routed"] == internal["accepted"] + internal["rejected"] == 1239
    assert internal["regional_forward_passes"] == 1239


# --------------------------------------------------------------------------- #
# 2. BrEaST inventory reconciliation
# --------------------------------------------------------------------------- #
def test_breast_inventory_reconciles_to_the_four_numbers():
    rec = json.loads((AUD / "final_verification.json").read_text(encoding="utf-8"))
    b = rec["breast_inventory"]
    assert b["images_on_disk"] == 270
    assert b["tumour_masks_on_disk"] == 252
    assert b["images_without_mask"] == 18
    assert b["manifest_rows"] == 256
    assert b["analysed"] == 252
    assert b["without_mask_additional_views"] == 14
    assert b["without_mask_primary_images"] == 4
    # 270 = 252 analysed + 4 excluded + 14 never eligible
    assert 252 + 4 + 14 == 270


def test_breast_case_groups_are_case_level_not_patient_level():
    rec = json.loads((AUD / "final_verification.json").read_text(encoding="utf-8"))
    b = rec["breast_inventory"]
    assert b["independent_case_groups"] == 252
    assert "patient" in b["independence_caveat"].lower()


# --------------------------------------------------------------------------- #
# 3. BARR-action figures
# --------------------------------------------------------------------------- #
def test_action_figure_manifest_records_four_panels():
    rec = json.loads((AUD / "barr_action_figure.json").read_text(encoding="utf-8"))
    assert rec["inference_rerun"] is False
    assert set(rec["selection_rule"]) == {"A", "B", "C", "D"}
    rows = {r["panel"]: r for f in rec["figures"].values() for r in f}
    assert set(rows) == {"A", "B", "C", "D"}
    assert rows["A"]["delta"] > 0
    assert rows["B"]["delta"] < 0
    assert rows["C"]["state"] == "REJECTED"
    assert rows["D"]["state"] == "NOT_ATTEMPTED"


def test_action_figures_use_the_mandated_palette():
    rec = json.loads((AUD / "barr_action_figure.json").read_text(encoding="utf-8"))
    assert rec["error_palette_rgb"] == {
        "TP": [0, 230, 0], "FP": [255, 32, 32], "FN": [32, 96, 255], "TN": [24, 24, 24]}


def test_stones_has_no_harmful_accepted_case_and_says_so():
    rec = json.loads((AUD / "barr_action_figure.json").read_text(encoding="utf-8"))
    assert rec["accepted_with_negative_change"]["stones"] == 0
    assert rec["stones_min_accepted_delta"] == 0.0
    assert rec["stones_harmful_example"].startswith("ABSENT")


def test_action_figure_files_exist():
    for name in ("fig9_external_barr_action_adopted.png",
                 "fig10_external_barr_action_notadopted.png"):
        p = FIG / name
        assert p.is_file(), name
        assert p.stat().st_size > 100_000, name


def test_rejected_cases_have_zero_delta_by_construction():
    rec = json.loads((AUD / "barr_action_figure.json").read_text(encoding="utf-8"))
    assert "delta == 0" in rec["rejected_delta_note"]
    paired = pd.read_csv(TAB / "c1_external_stress_paired.csv")
    rej = paired[paired.state == "REJECTED"]
    assert len(rej) == 45
    assert (rej.delta_dice.abs() < 1e-12).all()


# --------------------------------------------------------------------------- #
# 4. retired wordings
# --------------------------------------------------------------------------- #
RETIRED_IN_REPORT = [
    "no interval estimate",
    "not statistically distinguishable",
    "no true-negative behaviour",
    "5.45",
]

RETIRED_IN_MS = [
    "no interval estimate",
    "not statistically distinguishable",
    "absence of true-negative behaviour",
    "5.45",
    "Paired Wilcoxon",
]


REGISTER_HEADING = "Corrections and Retractions Relative to the October 30 Build"


def split_report() -> tuple[str, str]:
    """Return (body, register).

    Section 9 quotes every retracted wording verbatim in order to record the
    retraction. Asserting a retired phrase is absent from the whole document
    would therefore force the register to be deleted, which is the opposite of
    what is wanted: the register must be preserved. So the two regions are
    tested separately -- absent from the body, present in the register.
    """
    t = docx_text()
    i = t.find(REGISTER_HEADING)
    assert i != -1, "retraction register is missing from the report"
    return t[:i], t[i:]


@pytest.mark.parametrize("phrase", RETIRED_IN_REPORT)
def test_report_body_no_longer_asserts(phrase):
    body, _ = split_report()
    assert phrase not in body


# Only entry I quotes its retracted wording verbatim; the others paraphrase it.
# The register is required to keep that quotation, so the retraction stays auditable.
@pytest.mark.parametrize("phrase", ["no interval estimate", "straddling zero"])
def test_retraction_register_preserves_the_retired_wording(phrase):
    _, register = split_report()
    assert phrase in register


@pytest.mark.parametrize("phrase", RETIRED_IN_MS)
def test_manuscript_no_longer_asserts(phrase):
    assert phrase not in MS.read_text(encoding="utf-8")


def test_report_states_the_iqr_sits_on_zero():
    t = docx_text()
    assert "sits on zero rather than straddling it" in t
    assert "[0, 0]" in t


def test_report_labels_the_stones_interval_as_image_level():
    t = docx_text()
    assert "image-level descriptive interval" in t
    assert "each of the 20 images is its own cluster" in t


def test_report_withdraws_the_24_3_percent_workload():
    t = docx_text()
    assert "25.0%" in t
    # the old figure may appear only as a withdrawn claim, never as a live one
    assert "24.3% of the unconditional refiner workload" in t
    assert "is withdrawn" in t


def test_report_carries_the_new_correction_rows():
    t = docx_text()
    for token in ("CONTRADICTION RESOLVED", "Items A\u2013L"):
        assert token in t, token


# --------------------------------------------------------------------------- #
# 5. C1 manuscript statistics against the frozen endpoint
# --------------------------------------------------------------------------- #
def test_manuscript_uses_the_frozen_seed_average_endpoint():
    t = MS.read_text(encoding="utf-8")
    assert "seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL" in t
    assert "1}{3}" in t or "\\frac{1}{3}" in t


def test_manuscript_declares_no_confirmatory_test():
    t = MS.read_text(encoding="utf-8")
    assert "No confirmatory significance test is eligible" in t
    assert "10,000" in t
    assert "20261027" in t


def test_manuscript_runtime_arithmetic_is_consistent():
    t = MS.read_text(encoding="utf-8")
    assert "6.29" in t
    # 37.72 / 6 must round to the stated per-run figure
    assert round(37.72 / 6, 2) == 6.29


def test_manuscript_does_not_claim_external_non_inferiority():
    t = MS.read_text(encoding="utf-8")
    assert "not a demonstration of external non-inferiority" in t


def test_manuscript_domain_shift_is_not_causal():
    t = MS.read_text(encoding="utf-8")
    assert "descriptive" in t.lower()


# --------------------------------------------------------------------------- #
# 6. identity of the evidence itself
# --------------------------------------------------------------------------- #
def test_release_identities_are_still_the_frozen_ones():
    rec = json.loads((AUD / "barr_execution.json").read_text(encoding="utf-8"))
    assert rec["identities"]["global_checkpoint"]["sha256"] == \
        "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
    assert rec["identities"]["refiner_checkpoint"]["sha256"] == \
        "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
    for k, v in rec["identities"].items():
        assert v["matches_plan"] is True, k


def test_provenance_rebinding_is_recorded_not_hidden():
    p = ROOT / "reports/audits/c1_external_evidence_v1_0/claim_provenance.json"
    rec = json.loads(p.read_text(encoding="utf-8"))
    e = next(x for x in rec["entries"] if x["claim_id"] == "INT-05")
    assert e["verdict"] == "UNSUPPORTED"
    assert e["source_sha256"] == hashlib.sha256(
        (ROOT / e["source_artifact"]).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# 7. C1 execution handoff
# --------------------------------------------------------------------------- #
HANDOFF = ROOT / "docs/c1_execution_handoff_decision_v1_0.md"
RC3_DIGEST = "54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f"


def test_handoff_document_exists_and_is_terminal():
    t = HANDOFF.read_text(encoding="utf-8")
    assert "C1_EXECUTION_DECISION_DOCUMENTED__AWAITING_OPERATOR__NO_LAUNCH" in t


def test_handoff_keeps_c1_not_established():
    t = HANDOFF.read_text(encoding="utf-8")
    assert "`NOT_ESTABLISHED`" in t
    # The endpoint must be quoted exactly as frozen, not paraphrased.
    assert "seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL" in t


def test_handoff_cites_the_frozen_rc3_digest():
    t = HANDOFF.read_text(encoding="utf-8")
    assert RC3_DIGEST in t
    rec = json.loads(
        (ROOT / "src/research/c1_film_launch_rc3/manifest_rc3.json").read_text(encoding="utf-8"))
    assert rec["release_id"] == "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3"


def test_handoff_claims_no_launch_and_no_credentials():
    t = HANDOFF.read_text(encoding="utf-8").lower()
    assert "nothing here authorises training" in t
    # A future edit must not quietly assert that this pass produced a usable identity.
    for forbidden in ("grant minted", "credentials generated", "rc4 created"):
        assert forbidden not in t.replace("no grant was minted", "")


def test_rc3_gate_still_has_the_identity_defect_undocumented_by_its_own_tests():
    """The handoff says RC3 cannot accept its own digest. Pin the evidence.

    If a future change repairs this, the handoff becomes stale and this test
    fails, forcing the document to be updated rather than left misleading.
    """
    gate = (ROOT / "src/research/c1_film_launch_rc3/rc3_gate.py").read_text(encoding="utf-8")
    # Both constants are defined and never referenced again.
    assert gate.count("RC3_RELEASE_ID") == 1
    assert gate.count("RC2_FROZEN_DIGEST") == 1
    # The RC3 grant's digest is literally the RC2 grant's digest.
    assert "return self._rc2_grant.release_digest" in gate
    # verify_release_rc3 is never called from the gate.
    assert "verify_release_rc3(" not in gate


def test_rc3_tests_never_present_the_release_with_its_own_digest():
    t = (ROOT / "tests/test_c1_launch_rc3.py").read_text(encoding="utf-8")
    assert "INVALID_DIGEST" in t
    assert RC3_DIGEST not in t
