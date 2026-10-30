"""Phase 25B -- threshold semantics audit (work-order section 7).

The two thresholds have DISTINCT semantic roles and must never be conflated:

  ROI PROPOSAL threshold      = 0.30   (repository-authoritative v1.1 exact spec)
      -> ROI existence, bbox geometry, ROI size, ROI-derived descriptors

  SEGMENTATION OUTPUT threshold = 0.50  (INHERITED)
      -> the final binary segmentation mask / Dice / IoU

Work-order rule: do NOT automatically replace every 0.50 with 0.30, nor every
0.30 with 0.50. Every threshold-dependent feature must carry:
    feature_name, threshold_value, threshold_role, frozen_source
No ambiguous bare "threshold" field is allowed.

This audit is DEFINITIONAL and does not depend on the (currently blocked)
deep-feature reduction, so it can be produced now.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


ROI_PROPOSAL = 0.30
SEG_OUTPUT = 0.50

ROLES = {
    "ROI_PROPOSAL": {
        "value": ROI_PROPOSAL,
        "role": "ROI_PROPOSAL",
        "frozen_source": "phase24_exact_implementation_spec.json#router.roi.predicted_foreground_threshold",
        "governs": ["ROI existence", "bbox geometry", "ROI size",
                    "ROI-derived descriptors", "action availability"],
        "not_used_for": ["Dice", "IoU", "final binary mask"],
    },
    "SEGMENTATION_OUTPUT": {
        "value": SEG_OUTPUT,
        "role": "SEGMENTATION_OUTPUT",
        "frozen_source": "phase24_exact_implementation_spec.json#fusion.segmentation_threshold (INHERITED)",
        "governs": ["final binary segmentation mask", "Dice", "IoU"],
        "not_used_for": ["ROI geometry", "bbox existence"],
    },
}

# Every Phase25B threshold-dependent feature, with its governing role.
FEATURES = [
    ("pred_foreground_fraction", "ROI_PROPOSAL"),
    ("pred_foreground_pixels", "ROI_PROPOSAL"),
    ("pred_roi_exists", "ROI_PROPOSAL"),
    ("pred_empty", "ROI_PROPOSAL"),
    ("predicted_roi_area_fraction", "ROI_PROPOSAL"),
    ("predicted_roi_side", "ROI_PROPOSAL"),
    ("frac_prob_within_0p05_of_boundary", "UNDEFINED_IN_FROZEN_SPEC"),
    ("frac_prob_within_0p02_of_boundary", "UNDEFINED_IN_FROZEN_SPEC"),
    ("mean_boundary_margin", "UNDEFINED_IN_FROZEN_SPEC"),
    ("entropy_proxy_mean", "THRESHOLD_FREE"),
]


def main() -> int:
    rows = []
    for name, role_key in FEATURES:
        if role_key in ROLES:
            r = ROLES[role_key]
            rows.append({
                "feature_name": name,
                "threshold_value": r["value"],
                "threshold_role": r["role"],
                "frozen_source": r["frozen_source"],
            })
        elif role_key == "THRESHOLD_FREE":
            rows.append({
                "feature_name": name,
                "threshold_value": None,
                "threshold_role": "THRESHOLD_FREE",
                "frozen_source": ("p_global only; no binarisation threshold enters the "
                                  "definition"),
            })
        else:
            rows.append({
                "feature_name": name,
                "threshold_value": None,
                "threshold_role": role_key,
                "frozen_source": ("NOT FROZEN -- the Phase24 v1.1 artifact does not state "
                                  "which threshold this boundary-band statistic uses"),
            })

    ambiguous = [r for r in rows
                 if r["threshold_role"] in ("UNDEFINED_IN_FROZEN_SPEC", None, "")]
    bare_threshold_fields = [k for r in rows for k in r
                             if k == "threshold" or k.strip() == "threshold"]

    unresolved = [r["feature_name"] for r in rows
                  if r["threshold_role"] == "UNDEFINED_IN_FROZEN_SPEC"]

    verdict = ("PHASE25B_THRESHOLD_SEMANTICS_INCOMPLETE"
               if unresolved else "PHASE25B_THRESHOLD_SEMANTICS_OK")

    out = {
        "artifact": "phase25b_threshold_semantics_audit",
        "phase": "25B",
        "purpose": "keep the two threshold roles distinct; forbid a bare 'threshold' field",
        "roi_proposal_threshold": ROI_PROPOSAL,
        "segmentation_output_threshold": SEG_OUTPUT,
        "semantic_roles": ROLES,
        "feature_threshold_bindings": rows,
        "n_features": len(rows),
        "ambiguous_bare_threshold_fields": bare_threshold_fields,
        "features_with_unresolved_threshold_role": unresolved,
        "automatic_substitution_applied": False,
        "automatic_substitution_note": (
            "no 0.50 was blindly rewritten as 0.30, and no 0.30 was blindly rewritten as "
            "0.50; each feature is bound to an explicitly frozen role or declared "
            "UNRESOLVED"
        ),
        "verdict": verdict,
        "blocked_by": "phase25b_phase24_feature_spec_binding.json",
        "extraction_performed": False,
        "verdict_note": ("the boundary-band scalars cannot be bound to a threshold role "
                         "because Phase24 v1.1 never states one; this is one of the "
                         "documented causes of PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE"),
        "test_reads": 0,
        "holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
    }
    AUD.mkdir(parents=True, exist_ok=True)
    (AUD / "phase25b_threshold_semantics_audit.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for r in rows:
        print(f"{r['feature_name']:36s} thr={str(r['threshold_value']):5s} "
              f"role={r['threshold_role']}")
    print()
    print("bare 'threshold' fields:", bare_threshold_fields)
    print("unresolved roles:", unresolved)
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
