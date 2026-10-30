"""Phase 23 — reviewer-visual repair FINAL CHECK.

Verifies, from the actual artifacts on disk, every requirement of §13:

  * Phase-23 verdict unchanged
  * closest prior art unchanged
  * terminology unchanged
  * claim ladder unchanged
  * Phase-24 constraints unchanged
  * notebook has >= 4 valid figures
  * notebook has 0 errors
  * three builds byte-identical
  * TEST all zero
  * Phase 24 NOT_STARTED

Writes reports/audits/phase23_reviewer_visual_final_check.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase23_visual_final_check.py
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
FIG = ROOT / "reports" / "figures" / "phase23_novelty_audit"
NB = (ROOT / "notebooks/phasewise/phase_23_literature_novelty"
      / "phase23_literature_methodological_novelty_audit.ipynb")

TERMINAL = ("PHASE23_REVIEWER_VISUALS_COMPLETE__SCIENCE_UNCHANGED__"
            "PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED")


def _j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    verdict = _j(AUD / "phase23_novelty_verdict.json")
    ladder = _j(AUD / "phase23_novelty_claim_ladder.json")
    cf = _j(AUD / "phase23_counterfactual_terminology_audit.json")
    ct = _j(AUD / "phase23_certification_terminology_audit.json")
    pc = _j(AUD / "phase23_phase24_design_constraints.json")
    det = _j(AUD / "phase23_notebook_visual_determinism.json")
    integ = _j(AUD / "phase23_notebook_visual_integrity.json")
    prov = _j(AUD / "phase23_reviewer_visual_repair.json")

    # ---- 1. verdict unchanged ---------------------------------------------
    ck("verdict_label_unchanged",
       verdict.get("overall_label") == "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
       verdict.get("overall_label"))
    ck("verdict_max_claim_level_2", verdict.get("maximum_defensible_claim_level") == 2)
    ck("verdict_name_status_rename", verdict.get("recommended_method_name_status") == "RENAME")
    ck("verdict_algorithmic_occupied",
       verdict.get("algorithmic_novelty_status") == "OCCUPIED_AT_THE_MECHANISM_LEVEL")
    ck("verdict_problem_formulation_occupied",
       verdict.get("problem_formulation_novelty_status") == "OCCUPIED")
    ck("verdict_system_integration_unoccupied",
       verdict.get("system_integration_novelty_status") == "APPARENTLY_UNOCCUPIED")

    # ---- 2. novelty axes unchanged ----------------------------------------
    axes = {r["axis"]: r["status"] for r in
            __import__("csv").DictReader(
                (ROOT / "reports/tables/phase23_novelty_axes.csv").open(encoding="utf-8"))}
    ck("axis_A_occupied", axes.get("A") == "OCCUPIED", axes.get("A"))
    ck("axis_B_not_occupied_as_learned_segmentation_target",
       axes.get("B") == "NOT_OCCUPIED_AS_A_LEARNED_SEGMENTATION_TARGET", axes.get("B"))
    ck("axis_C_partially_occupied", axes.get("C") == "PARTIALLY_OCCUPIED", axes.get("C"))
    ck("axis_D_not_occupied_as_combination",
       axes.get("D") == "NOT_OCCUPIED_AS_A_COMBINATION", axes.get("D"))

    # ---- 3. terminology unchanged -----------------------------------------
    ck("terminology_counterfactual",
       cf.get("outcome") == "PREFER_PAIRED_REFINEMENT_GAIN", cf.get("outcome"))
    ck("terminology_certification",
       ct.get("recommendation") == "USE_BENEFIT_AWARE_ONLY", ct.get("recommendation"))

    # ---- 4. claim ladder unchanged ----------------------------------------
    ck("claim_ladder_max_level_2", ladder.get("recommended_maximum_level") == 2)
    lv3 = next((l for l in ladder.get("levels", []) if l.get("level") == 3), {})
    ck("claim_ladder_level3_not_supported",
       "NO" in str(lv3.get("defensible_for_our_candidate", "")), lv3.get("template"))

    # ---- 5. Phase-24 constraints unchanged --------------------------------
    ck("phase24_constraints_eligible_not_started",
       pc.get("status") == "PHASE24_ELIGIBLE_NOT_STARTED", pc.get("status"))
    ck("phase24_constraints_present",
       len(pc.get("high_level_constraints", [])) >= 10,
       f"{len(pc.get('high_level_constraints', []))} constraints")
    ck("phase24_constraints_no_architecture_decided",
       "No architecture" in str(pc.get("scope", "")), pc.get("scope", "")[:60])

    # ---- 6. no phase24 artifact -------------------------------------------
    p24 = list(AUD.glob("phase24_*")) + list((ROOT / "reports/tables").glob("phase24_*"))
    ck("phase24_not_started", len(p24) == 0, f"{len(p24)} phase24 artifacts")

    # ---- 7. science artifacts unchanged vs the Phase-23 freeze -------------
    ck("science_untouched_verification",
       prov.get("science_untouched_verification", {}).get("n_changed") == 0,
       f"{prov.get('science_untouched_verification', {}).get('n_verified')} verified / "
       f"{prov.get('science_untouched_verification', {}).get('n_changed')} changed")
    ck("prior_art_matrix_changed_false", prov.get("prior_art_matrix_changed") is False)
    ck("closest_prior_unchanged", prov.get("literature_classification_changed") is False)
    ck("no_papers_added_or_removed",
       prov.get("retained_papers_added_or_removed") is False)

    # ---- 8. notebook figures: >= 4 valid, validated from the actual bytes --
    nb = _j(NB)
    pngs = []
    for ci, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        for o in c.get("outputs", []) or []:
            d = o.get("data", {}) or {}
            if "image/png" in d:
                v = d["image/png"]
                if isinstance(v, list):
                    v = "".join(v)
                raw = base64.b64decode(v, validate=True)
                im = Image.open(io.BytesIO(raw))
                im.verify()
                pngs.append({"cell_index": ci, "cell_id": c.get("id"), "bytes": len(raw),
                             "sha256": hashlib.sha256(raw).hexdigest()})
    ck("notebook_has_at_least_4_figures", len(pngs) >= 4, f"{len(pngs)} valid PNG outputs")
    ck("notebook_visual_integrity_gate_pass", integ.get("all_passed") is True)
    ck("visual_integrity_required_4_4",
       integ.get("expected_required_figures") == 4
       and integ.get("embedded_required_figures") == 4
       and integ.get("valid_required_figures") == 4)
    ck("visual_integrity_zero_corrupt", integ.get("corrupt") == 0)
    ck("visual_integrity_no_missing", integ.get("missing") == [])
    ck("visual_integrity_no_unexpected", integ.get("unexpected") == [])
    ck("visual_integrity_no_unintended_duplicates",
       integ.get("unintended_duplicates") == [])

    # ---- 9. notebook executes cleanly -------------------------------------
    code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    errors = sum(1 for c in code_cells for o in (c.get("outputs") or [])
                 if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in code_cells]
    monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
    ck("notebook_zero_errors", errors == 0, f"{errors} tracebacks")
    ck("notebook_monotonic_exec_counts", monotonic)
    ck("notebook_has_html_tables",
       sum(1 for c in code_cells for o in (c.get("outputs") or [])
           if "text/html" in (o.get("data", {}) or {})) >= 2)

    # ---- 10. determinism ---------------------------------------------------
    shas = det.get("three_build_sha256", [])
    ck("three_builds_byte_identical", len(set(shas)) == 1 and len(shas) == 3,
       f"{len(set(shas))} distinct of {len(shas)}")
    ck("figures_three_builds_byte_identical",
       det.get("figures_three_builds_byte_identical") is True)
    ck("notebook_sha_matches_determinism",
       sha(NB) == det.get("new_notebook_sha256"), (sha(NB) or "")[:16])
    ck("notebook_sha_matches_integrity",
       sha(NB) == integ.get("notebook_sha256"))

    # ---- 11. TEST lock + no training/inference ----------------------------
    ck("test_reads_zero",
       all(x.get("test_reads") == 0 for x in (prov, det, integ)),
       str(prov.get("test_reads")))
    ck("no_training", prov.get("training") is False and prov.get("inference") is False)
    ck("no_search_rerun", prov.get("search_rerun") is False)
    ck("no_web_access_from_notebook", prov.get("governance", {}).get("web_access_from_notebook") is False)

    # ---- 12. figure inventory on disk -------------------------------------
    on_disk = sorted(p.name for p in FIG.glob("p23_*.png"))
    ck("figure_files_on_disk_5", len(on_disk) == 5, str(on_disk))
    ck("figure_manifest_present", (FIG / "phase23_figure_manifest.json").exists())

    n_pass = sum(1 for _, ok, _ in checks if ok)
    n_fail = len(checks) - n_pass

    out = {
        "artifact": "phase23_reviewer_visual_final_check",
        "phase": 23,
        "classification": "REVIEWER_PRESENTATION_REPAIR",
        "n_checks": len(checks),
        "n_passed": n_pass,
        "n_failed": n_fail,
        "all_passed": n_fail == 0,
        "checks": [{"check": n, "pass": ok, "detail": d} for n, ok, d in checks],
        "notebook_sha256": sha(NB),
        "n_valid_figure_outputs": len(pngs),
        "terminals": {
            "phase23_audit": "PHASE23_NOVELTY_AUDIT_COMPLETE__PARTIALLY_OCCUPIED__"
                              "PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED",
            "visual_repair": TERMINAL,
        },
        "terminal_state": TERMINAL,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "test_reads": 0,
    }
    (AUD / "phase23_reviewer_visual_final_check.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")

    for n, ok, d in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n}" + (f"   [{d}]" if d and not ok else ""))
    print()
    print(f"{n_pass}/{len(checks)} checks passed")
    print()
    if n_fail:
        print("FAIL-CLOSED: final check FAILED")
        return 1
    print(TERMINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
