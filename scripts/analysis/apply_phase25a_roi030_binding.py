"""Phase 25A (CANONICAL) — apply the ROI-threshold adjudication to the v1.1 binding.

The original ``build_phase25a_bindings.py`` recorded a *reported* discrepancy: the
Phase-24 v1.1 exact spec carries ``roi.predicted_foreground_threshold = 0.3`` while
the now-superseded Phase-25A execution bound 0.5. That discrepancy has since been
adjudicated as a FROZEN_SPEC_CLARIFICATION__NOT_SCIENCE_CHANGE:

    ROI PROPOSAL threshold        = 0.30   (drives the ROI bbox / ACTION_AVAILABLE)
    SEGMENTATION OUTPUT threshold = 0.50   (inherited evaluation mask threshold)

This script rewrites ``reports/audits/phase25a_phase24_v1_1_binding.json`` so the
bound ROI proposal threshold is the repository-authoritative 0.30, and replaces the
"REPORTED_NOT_SILENTLY_REPAIRED" discrepancy with an explicit adjudication entry.
Nothing is erased: the historical 0.5 binding and its rationale are retained verbatim
under ``discrepancies[0].historical`` and the adjudication pointer is added.

This is an EXECUTION-MECHANISM / BOOKKEEPING correction, NOT a science change:
no architecture, split, seed, or evaluation rule is altered.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/apply_phase25a_roi030_binding.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

ROI_PROPOSAL_THRESHOLD = 0.30
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
UTC = datetime.now(timezone.utc).isoformat()


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    path = AUD / "phase25a_phase24_v1_1_binding.json"
    if not path.exists():
        print(f"FAIL-CLOSED: missing {path}")
        return 2

    original = json.loads(path.read_text(encoding="utf-8"))
    original_sha = sha(path)

    # Preserve the historical discrepancy object verbatim.
    hist_disc = (original.get("discrepancies") or [{}])[0]
    if hist_disc.get("phase25a_bound_value") != 0.5:
        print("WARN: historical discrepancy no longer records a 0.5 binding; "
              f"found {hist_disc.get('phase25a_bound_value')!r}")

    adjudication_sha = sha(AUD / "phase24_phase25_roi_threshold_adjudication.json")
    supersession_sha = sha(AUD / "phase25a_roi050_supersession.json")

    adjudicated = {
        "field": "roi.predicted_foreground_threshold",
        "classification": "FROZEN_SPEC_CLARIFICATION__NOT_SCIENCE_CHANGE",
        "phase24_v1_1_frozen_value": 0.3,
        "bound_value_now": ROI_PROPOSAL_THRESHOLD,
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "segmentation_output_threshold_field": "fusion.segmentation_threshold",
        "segmentation_output_threshold_source": "INHERITED",
        "disagreement": False,
        # The ORIGINAL status is deliberately retained so the historical fact that the
        # conflict was once REPORTED (not silently repaired) remains on the record.
        "status": "REPORTED_NOT_SILENTLY_REPAIRED",
        "original_status": "REPORTED_NOT_SILENTLY_REPAIRED",
        "adjudication_status": "ADJUDICATED_FROZEN_SPEC_CLARIFICATION",
        "resolution": "The two fields have distinct semantic roles and must never be "
                      "conflated. ROI PROPOSAL = 0.30 (predicted-foreground mask / bbox / "
                      "ACTION_AVAILABLE). SEGMENTATION OUTPUT = 0.50 (inherited final-mask "
                      "threshold; NOT used for ROI). The earlier 0.5 ROI binding is SUPERSEDED.",
        "superseded_bound_value": 0.5,
        "phase24_science_changed": False,
        "phase24_exact_spec_changed": False,
        "adjudication_artifact": "reports/audits/phase24_phase25_roi_threshold_adjudication.json",
        "adjudication_sha256": adjudication_sha,
        "supersession_artifact": "reports/audits/phase25a_roi050_supersession.json",
        "supersession_sha256": supersession_sha,
        "historical": hist_disc,
        "test_reads": 0,
    }

    updated = dict(original)
    updated["bound_roi"] = dict(original["bound_roi"])
    updated["bound_roi"]["predicted_foreground_threshold"] = ROI_PROPOSAL_THRESHOLD
    updated["bound_roi"]["roi_proposal_threshold"] = ROI_PROPOSAL_THRESHOLD
    updated["bound_roi"]["segmentation_output_threshold"] = SEGMENTATION_OUTPUT_THRESHOLD
    updated["discrepancies"] = [adjudicated]
    updated["n_discrepancies"] = 1
    updated["discrepancy_status"] = "ADJUDICATED_FROZEN_SPEC_CLARIFICATION"
    updated["pre_adjudication_binding_sha256"] = original_sha
    updated["adjudication_applied"] = True
    updated["classification"] = "CANONICAL_PHASE25A_AFTER_THRESHOLD_ADJUDICATION"
    updated["test_reads"] = 0

    path.write_text(json.dumps(updated, indent=1) + "\n", encoding="utf-8")

    print(f"bound ROI proposal threshold -> {ROI_PROPOSAL_THRESHOLD}")
    print(f"segmentation output threshold -> {SEGMENTATION_OUTPUT_THRESHOLD}")
    print(f"pre-adjudication binding sha256: {original_sha}")
    print(f"historical discrepancy retained : "
          f"{hist_disc.get('status')} (bound {hist_disc.get('phase25a_bound_value')})")
    print("PHASE25A_ROI030_BINDING_ADJUDICATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
