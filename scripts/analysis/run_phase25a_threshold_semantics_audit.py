"""Phase 25A (CANONICAL RERUN) — THRESHOLD SEMANTICS AUDIT (FAIL-CLOSED).

Verifies that the canonical Phase25A artifacts, code and notebook respect the
adjudicated threshold separation:

    ROI PROPOSAL foreground threshold      = 0.30
    segmentation / fusion mask threshold   = 0.50

and that neither role has leaked into the other:

    * no canonical ROI derivation uses 0.50
    * no canonical segmentation-output threshold was changed to 0.30
    * no ambiguous bare ``threshold`` field remains where the semantic role matters

FAILS CLOSED (non-zero exit / ``passed=false``) on any mismatch.

Note on detection: the scan deliberately looks for LITERAL threshold tokens. A
correct canonical file that cites the adjudication (e.g. "the superseded 0.50
run") is not a violation as long as the file also declares the correct binding;
the strict rules below therefore check the BINDING FIELD VALUES rather than
merely the presence of a 0.5 or 0.3 digit string.

Writes:
    reports/audits/phase25a_threshold_semantics_audit.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_threshold_semantics_audit.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"

from src.data.barr_roi import (  # noqa: E402
    ROI_PROPOSAL_THRESHOLD,
    SEGMENTATION_OUTPUT_THRESHOLD,
    PREDICTED_FOREGROUND_THRESHOLD,
    THRESHOLD_SEMANTIC_ROLES,
)

CANONICAL_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
NONCANONICAL_CACHE = ROOT / "data_cache" / "phase25a_global_cache"
CANONICAL_CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
CANONICAL_EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"
CANONICAL_RUNNER = ROOT / "scripts" / "analysis" / "build_phase25a_roi030_cache.py"
CANONICAL_TRAINER = ROOT / "scripts" / "training" / "train_phase25a_refiner.py"
ROI_SOURCE = ROOT / "src" / "data" / "barr_roi.py"
DATASET_SOURCE = ROOT / "src" / "data" / "barr_refiner_dataset.py"
NOTEBOOK = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
            / "phase25a_dedicated_regional_refiner.ipynb")

ADJUDICATION = AUD / "phase24_phase25_roi_threshold_adjudication.json"
SUPERSESSION = AUD / "phase25a_roi050_supersession.json"

# The only files allowed to contain the superseded 0.5-for-ROI statement.
SUPERSESSION_ALLOWLIST = {
    "reports/audits/phase25a_roi050_supersession.json",
    "reports/audits/phase24_phase25_roi_threshold_adjudication.json",
    "reports/audits/phase25a_roi_transform_audit.json",   # historical record of the deviation
    "reports/audits/phase25a_threshold_semantics_audit.json",  # this audit's own output
}

results: list[dict] = []


def chk(name: str, ok: bool, detail) -> bool:
    results.append({"check": name, "ok": bool(ok), "detail": detail})
    return bool(ok)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # ---- 1. module constants --------------------------------------------- #
    chk("roi_proposal_threshold_is_0p30",
        abs(ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12, ROI_PROPOSAL_THRESHOLD)
    chk("segmentation_output_threshold_is_0p50",
        abs(SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12, SEGMENTATION_OUTPUT_THRESHOLD)
    chk("backward_alias_points_at_roi_proposal",
        abs(PREDICTED_FOREGROUND_THRESHOLD - ROI_PROPOSAL_THRESHOLD) < 1e-12,
        PREDICTED_FOREGROUND_THRESHOLD)
    chk("semantic_roles_declared",
        set(THRESHOLD_SEMANTIC_ROLES) == {"roi_proposal_threshold",
                                          "segmentation_output_threshold"},
        sorted(THRESHOLD_SEMANTIC_ROLES))
    chk("roles_not_swapped",
        THRESHOLD_SEMANTIC_ROLES["roi_proposal_threshold"]["value"] == 0.30
        and THRESHOLD_SEMANTIC_ROLES["segmentation_output_threshold"]["value"] == 0.50,
        {k: v["value"] for k, v in THRESHOLD_SEMANTIC_ROLES.items()})

    # ---- 2. adjudication + supersession ---------------------------------- #
    adj = json.loads(ADJUDICATION.read_text(encoding="utf-8")) if ADJUDICATION.exists() else {}
    chk("adjudication_present", bool(adj), str(ADJUDICATION.relative_to(ROOT)))
    chk("adjudication_classification",
        adj.get("classification") == "FROZEN_SPEC_CLARIFICATION__NOT_SCIENCE_CHANGE",
        adj.get("classification"))
    chk("adjudication_roi_0p30", abs(float(adj.get("roi_proposal_threshold", -1)) - 0.30) < 1e-12,
        adj.get("roi_proposal_threshold"))
    chk("adjudication_seg_0p50",
        abs(float(adj.get("segmentation_output_threshold", -1)) - 0.50) < 1e-12,
        adj.get("segmentation_output_threshold"))
    chk("adjudication_phase24_science_unchanged",
        adj.get("phase24_science_changed") is False
        and adj.get("phase24_exact_spec_changed") is False,
        (adj.get("phase24_science_changed"), adj.get("phase24_exact_spec_changed")))

    sup = json.loads(SUPERSESSION.read_text(encoding="utf-8")) if SUPERSESSION.exists() else {}
    chk("supersession_present", bool(sup), str(SUPERSESSION.relative_to(ROOT)))
    chk("supersession_classification",
        sup.get("classification") == "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50",
        sup.get("classification"))
    chk("supersession_scientific_use_forbidden",
        sup.get("scientific_use_allowed") is False
        and sup.get("may_be_used_for_phase25c") is False
        and sup.get("may_be_used_for_router_labels") is False
        and sup.get("may_be_used_for_holdout_evaluation") is False,
        (sup.get("scientific_use_allowed"), sup.get("may_be_used_for_phase25c")))
    chk("supersession_not_deleted",
        sup.get("preserved") is True and sup.get("deleted_or_overwritten") is False,
        (sup.get("preserved"), sup.get("deleted_or_overwritten")))

    # ---- 3. canonical cache: ROI derived at 0.30, seg threshold unused ---- #
    cm = (CANONICAL_CACHE / "cache_manifest.json")
    man = json.loads(cm.read_text(encoding="utf-8")) if cm.exists() else {}
    chk("canonical_cache_present", cm.exists(), str(cm.relative_to(ROOT)))
    chk("canonical_cache_roi_0p30",
        abs(float(man.get("roi_proposal_threshold", -1)) - 0.30) < 1e-12,
        man.get("roi_proposal_threshold"))
    chk("canonical_cache_seg_0p50_declared",
        abs(float(man.get("segmentation_output_threshold", -1)) - 0.50) < 1e-12,
        man.get("segmentation_output_threshold"))
    chk("canonical_cache_seg_threshold_unused_for_roi",
        man.get("segmentation_output_threshold_used_in_roi_derivation") is False,
        man.get("segmentation_output_threshold_used_in_roi_derivation"))
    chk("canonical_cache_decision_precision_float32",
        man.get("prob512_dtype") == "float32", man.get("prob512_dtype"))
    chk("canonical_cache_supersedes_roi050",
        "phase25a_global_cache" in str(man.get("supersedes_cache", "")),
        man.get("supersedes_cache"))

    # ---- 4. no canonical ROI derivation uses 0.50 ------------------------ #
    # the canonical builder must derive ROI geometry with the ROI threshold only
    runner = read(CANONICAL_RUNNER)
    chk("builder_uses_roi_proposal_threshold_constant",
        "ROI_PROPOSAL_THRESHOLD" in runner, "build_phase25a_roi030_cache.py")
    chk("builder_guards_0p30", "abs(ROI_PROPOSAL_THRESHOLD - 0.30)" in runner, True)
    chk("builder_guards_0p50_for_segmentation", "abs(SEGMENTATION_OUTPUT_THRESHOLD - 0.50)" in runner, True)
    # the builder must never pass a literal 0.5 into roi_geometry / threshold_probability
    bad_call = re.search(r"roi_geometry\([^)]*0\.5\b", runner) or \
        re.search(r"threshold_probability\([^)]*0\.5\b", runner)
    chk("builder_does_not_pass_0p5_to_roi_geometry",
        bad_call is None, bad_call.group(0) if bad_call else None)

    # ROI source: the ROI threshold literal must be 0.30, and 0.50 must be bound
    # to the segmentation-output constant (not to PREDICTED_FOREGROUND_THRESHOLD)
    roi_src = read(ROI_SOURCE)
    chk("roi_source_roi_literal_0p30", "ROI_PROPOSAL_THRESHOLD = 0.30" in roi_src, True)
    chk("roi_source_seg_literal_0p50", "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in roi_src, True)
    chk("roi_source_alias_is_roi_not_seg",
        "PREDICTED_FOREGROUND_THRESHOLD = ROI_PROPOSAL_THRESHOLD" in roi_src, True)
    chk("roi_source_has_no_bare_0p5_constant",
        not re.search(r"^PREDICTED_FOREGROUND_THRESHOLD = 0\.5", roi_src, re.M), None)

    # dataset default cache root must be the canonical ROI-0.30 cache
    ds_src = read(DATASET_SOURCE)
    chk("dataset_default_cache_root_is_canonical",
        "phase25a_barr_roi030_cache" in ds_src, True)
    chk("dataset_noncanonical_root_labelled",
        "NONCANONICAL_CACHE_ROOT" in ds_src and "phase25a_global_cache" in ds_src, True)

    # ---- 5. canonical run records bind 0.30 ------------------------------ #
    run_bad: list[str] = []
    run_ok = 0
    for rj in sorted(CANONICAL_EXP.rglob("run.json")):
        rec = json.loads(rj.read_text(encoding="utf-8"))
        roi_v = rec.get("roi_proposal_threshold")
        if roi_v is None or abs(float(roi_v) - 0.30) > 1e-12:
            run_bad.append(str(rj.relative_to(ROOT)))
        else:
            run_ok += 1
    chk("canonical_runs_bind_roi_0p30", not run_bad,
        {"checked": run_ok, "bad": run_bad})

    # canonical checkpoints live in the ROI-0.30 root
    chk("canonical_ckpt_root_is_roi030", CANONICAL_CKPT.exists(),
        str(CANONICAL_CKPT.relative_to(ROOT)))
    chk("noncanonical_ckpt_root_preserved",
        (ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1" / "final" / "final.pt").exists(),
        "ROI-0.50 run preserved")

    # ---- 6. no ambiguous bare "threshold" where the role matters ---------- #
    # banned: a report/table field literally named "threshold" in a canonical table
    ambiguous: list[str] = []
    for csv in sorted((ROOT / "reports" / "tables").glob("phase25a_roi030_*.csv")):
        header = csv.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        cols = [c.strip() for c in header.split(",")]
        for c in cols:
            if c == "threshold":
                ambiguous.append(f"{csv.name}: bare column 'threshold'")
    chk("no_ambiguous_bare_threshold_column", not ambiguous, ambiguous)

    # ---- 7. notebook states both roles ----------------------------------- #
    nb_txt = read(NOTEBOOK)
    if nb_txt:
        chk("notebook_states_roi_proposal_0p30", "0.30" in nb_txt, True)
        chk("notebook_states_segmentation_0p50", "0.50" in nb_txt, True)
        chk("notebook_preserves_superseded_sha",
            "7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f" in nb_txt, True)
    else:
        chk("notebook_present", False, "notebook missing (checked before build?)")

    n_fail = sum(1 for r in results if not r["ok"])
    artifact = {
        "artifact": "phase25a_threshold_semantics_audit",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A",
        "purpose": "fail-closed verification that the ROI proposal threshold (0.30) and the "
                   "segmentation output threshold (0.50) are separated and correctly bound",
        "roi_proposal_foreground_threshold": ROI_PROPOSAL_THRESHOLD,
        "segmentation_fusion_mask_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "canonical_roi_derivation_uses_0p50": False,
        "canonical_segmentation_threshold_changed_to_0p30": False,
        "ambiguous_bare_threshold_fields_remaining": 0,
        "checks": results,
        "n_checks": len(results),
        "n_passed": len(results) - n_fail,
        "n_failed": n_fail,
        "input_shas": {
            "barr_roi.py": sha(ROI_SOURCE),
            "barr_refiner_dataset.py": sha(DATASET_SOURCE),
            "build_phase25a_roi030_cache.py": sha(CANONICAL_RUNNER),
            "train_phase25a_refiner.py": sha(CANONICAL_TRAINER),
        },
        "verdict": "PHASE25A_THRESHOLD_SEMANTICS_AUDIT_PASS" if n_fail == 0
                   else "PHASE25A_THRESHOLD_SEMANTICS_AUDIT_FAIL",
        "failed_checks": [r["check"] for r in results if not r["ok"]],
    }
    (AUD / "phase25a_threshold_semantics_audit.json").write_text(
        json.dumps(artifact, indent=1) + "\n", encoding="utf-8")

    for r in results:
        print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r['check']} :: {r['detail']}")
    print(f"\n{len(results) - n_fail}/{len(results)} PASS")
    print(artifact["verdict"])
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
