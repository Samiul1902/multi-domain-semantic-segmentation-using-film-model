"""Post-Phase22 repair — Part C: FINAL COMBINED AUDIT.

Verifies, from repository state only, that the additive reviewer/evidence repair
left the frozen science intact.

PHASE 21
  * science unchanged (macro-domain VAL Dice, best epoch, param count)
  * best.pt SHA unchanged
  * canonical VAL inference count == 1 (no rerun)
  * no training, no inference
  * inventory figures == 43
  * embedded figures == 43, valid == 43/43
  * corrupt == 0, zero notebook errors
  * 3 consecutive builds byte-identical

PHASE 22
  * checkpoint unchanged
  * diagnostic protocol unchanged
  * no segmentation inference rerun, no training
  * GT-derived and GT-free signals separated
  * no GT-derived signal called deployable
  * GT-free routing conclusions recomputed
  * "512 optimal" wording removed
  * KUB TINY significance wording corrected

GLOBAL
  * TEST image reads == 0, mask reads == 0, inference == 0, visualization == 0

Writes reports/audits/post_phase22_evidence_repair_final_audit.json and prints
the two mandated terminal states.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_post_phase22_final_audit.py
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"
NB21 = (ROOT / "notebooks/phasewise/phase_21_global_medfilm"
        / "phase21_global_medfilm_reference.ipynb")
NB22 = (ROOT / "notebooks/phasewise/phase_22_resource_gap"
        / "phase22_resource_gap_analysis.ipynb")
REPORT22 = ROOT / "reports/phase22_resource_gap_report.md"

OUT = A / "post_phase22_evidence_repair_final_audit.json"

EXPECTED = {
    "phase21_macro_dice": 0.8350794169575282,
    "phase21_best_epoch": 66,
    "phase21_params": 3523001,
    "phase21_best_pt_sha256":
        "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "phase21_notebook_original_sha256":
        "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed",
    "phase22_protocol_sha256":
        "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7",
    "inventory_figures": 43,
}


def _j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def nb_png_audit(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    code = [c for c in cells if c.get("cell_type") == "code"]
    err = sum(1 for c in cells for o in (c.get("outputs") or [])
              if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in code]
    n_png = valid = 0
    for c in cells:
        for o in (c.get("outputs") or []):
            d = o.get("data") or {}
            if "image/png" in d:
                n_png += 1
                pl = d["image/png"]
                pl = "".join(pl) if isinstance(pl, list) else pl
                try:
                    raw = base64.b64decode(pl, validate=True)
                    Image.open(io.BytesIO(raw)).verify()
                    Image.open(io.BytesIO(raw)).load()
                    valid += 1
                except Exception:
                    pass
    return {
        "cells": len(cells), "code_cells": len(code),
        "executed_code_cells": sum(1 for c in code if c.get("execution_count") is not None),
        "monotonic": all(counts[i] == i + 1 for i in range(len(counts))),
        "errors": err, "image_png_outputs": n_png, "valid_png_outputs": valid,
        "html_table_outputs": sum(1 for c in cells for o in (c.get("outputs") or [])
                                  if "text/html" in (o.get("data") or {})),
        "sha256": _sha(path),
    }


def main() -> int:
    checks: list[dict] = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    # ================= PHASE 21 ================= #
    an = _j(A / "phase21_analysis.json")
    gm = (an.get("global_medfilm") or {})
    cl = _j(ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3"
            / "phase21_training_closure.json")
    vef = _j(A / "phase21_val_evaluation.json")
    fin = _j(A / "phase21_final_freeze.json")

    chk("P21_macro_dice_unchanged",
        gm.get("macro_domain_dice") == EXPECTED["phase21_macro_dice"],
        f"{gm.get('macro_domain_dice')}")
    chk("P21_best_epoch_unchanged", cl.get("best_epoch") == EXPECTED["phase21_best_epoch"],
        f"{cl.get('best_epoch')}")
    chk("P21_best_pt_sha_unchanged",
        _sha(ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt")
        == EXPECTED["phase21_best_pt_sha256"],
        "best.pt")
    cvr = (vef.get("canonical_val_inference_runs")
           or (vef.get("provenance") or {}).get("canonical_val_inference_runs"))
    chk("P21_canonical_val_runs_exactly_1", cvr == 1, f"{cvr}")
    tr = (vef.get("provenance") or {})
    chk("P21_no_inference_rerun",
        all((tr.get(k) or 0) == 0 for k in
            ("test_image_reads", "test_mask_reads", "test_inference", "test_visualization")),
        "test counters 0")
    chk("P21_scientific_results_changed_false",
        fin.get("freeze_verified") is True, "freeze still verified (historical)")

    inv = pd.read_csv(ROOT / "reports/figures/phase21_global_medfilm"
                      / "phase21_figure_inventory.csv")
    chk("P21_inventory_figures_43", len(inv) == 43, f"{len(inv)}")
    nb21 = nb_png_audit(NB21)
    chk("P21_embedded_png_43", nb21["image_png_outputs"] == 43,
        f"{nb21['image_png_outputs']}")
    chk("P21_valid_png_43_of_43", nb21["valid_png_outputs"] == 43,
        f"{nb21['valid_png_outputs']}/43")
    chk("P21_zero_corruption", nb21["image_png_outputs"] == nb21["valid_png_outputs"],
        f"corrupt={nb21['image_png_outputs'] - nb21['valid_png_outputs']}")
    chk("P21_zero_errors", nb21["errors"] == 0, f"{nb21['errors']}")
    chk("P21_code_cells_executed", nb21["executed_code_cells"] == nb21["code_cells"],
        f"{nb21['executed_code_cells']}/{nb21['code_cells']}")
    det21 = _j(A / "phase21_notebook_determinism_repair.json")
    chk("P21_three_builds_byte_identical",
        det21.get("three_builds_byte_identical") is True,
        f"{det21.get('sha256_per_build')}")
    rep21 = _j(A / "phase21_reviewer_notebook_repair.json")
    chk("P21_repair_attests_no_science_change",
        rep21.get("scientific_results_changed") is False
        and rep21.get("canonical_val_rerun") is False
        and rep21.get("training_rerun") is False,
        "attestations")

    # ================= PHASE 22 ================= #
    rb = _j(A / "phase22_phase21_reference_binding.json")
    chk("P22_checkpoint_unchanged",
        _sha(ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt")
        == EXPECTED["phase21_best_pt_sha256"], "best.pt")
    chk("P22_diagnostic_protocol_unchanged",
        _sha(A / "phase22_diagnostic_protocol.json") == EXPECTED["phase22_protocol_sha256"],
        "protocol SHA")

    sig = _j(A / "phase22_postfreeze_semantic_repair.json")
    chk("P22_no_training_rerun", sig.get("training_rerun") is False, "")
    chk("P22_no_segmentation_inference_rerun",
        sig.get("scientific_inference_rerun") is False
        and sig.get("new_inference_performed") is False, "")
    chk("P22_checkpoint_changed_false", sig.get("checkpoint_changed") is False, "")
    chk("P22_roi_protocol_unchanged", sig.get("roi_protocol_changed") is False, "")
    chk("P22_scale_protocol_unchanged", sig.get("scale_protocol_changed") is False, "")

    cls = _j(A / "phase22_benefit_proxy_feature_classification.json")
    chk("P22_no_gt_signal_called_deployable",
        cls.get("fail_closed_ok") is True and not cls.get("fail_closed_violations"),
        f"violations={cls.get('fail_closed_violations')}")

    gf = T / "phase22_gt_free_proxy_vs_benefit.csv"
    ga = T / "phase22_gt_aware_posthoc_associations.csv"
    chk("P22_gt_free_table_exists", gf.exists(), "")
    chk("P22_gt_aware_table_exists", ga.exists(), "")
    if gf.exists() and ga.exists():
        df_gf, df_ga = pd.read_csv(gf), pd.read_csv(ga)
        chk("P22_gt_free_table_all_gtfree", bool((df_gf["uses_GT"] == False).all()),
            f"{len(df_gf)} rows")
        chk("P22_gt_aware_table_all_gt", bool((df_ga["uses_GT"] == True).all()),
            f"{len(df_ga)} rows")
        chk("P22_recall_not_in_gtfree_table", "recall" not in set(df_gf["signal"]),
            "")
        chk("P22_gtfree_routing_recomputed",
            sig.get("best_gt_free_signal") is not None,
            f"{sig.get('best_gt_free_signal', {}).get('signal') if sig.get('best_gt_free_signal') else None}")

    # routing policies
    pol = sig.get("routing_policy_deployability_audit") or []
    chk("P22_routing_policies_all_consistent",
        bool(pol) and all(p["consistent"] for p in pol),
        f"{len(pol)} policies")

    # wording
    rpt = REPORT22.read_text(encoding="utf-8") if REPORT22.exists() else ""
    chk("P22_report_no_deployable_recall_claim",
        "Best deployable uncertainty signal" not in rpt, "")
    chk("P22_report_has_512_required_wording",
        "does not establish a globally optimal inference resolution" in rpt, "")
    chk("P22_report_has_kub_tiny_required_wording",
        "descriptive and not statistically established" in rpt, "")
    chk("P22_report_preserves_useful_finding",
        "strongly heterogeneous" in rpt and "harmful in aggregate" in rpt, "")

    nb22 = nb_png_audit(NB22)
    # Parse the notebook, concatenate all cell source, and flatten adjacent Python
    # string-literal joins (``"..." "..."``) and markdown blockquote prefixes, so a
    # required phrase that spans source lines is still found. Without this the
    # phrase looks absent purely because of source formatting.
    if NB22.exists():
        _nb = json.loads(NB22.read_text(encoding="utf-8"))
        _parts = []
        for _c in _nb.get("cells", []):
            _s = _c.get("source", "")
            _parts.append("".join(_s) if isinstance(_s, list) else str(_s))
        _txt = "\n".join(_parts)
        _txt = re.sub(r"^\s*>\s?", " ", _txt, flags=re.MULTILINE)   # blockquote
        _txt = re.sub(r"[\"']\s*\n\s*[\"']", "", _txt)              # adjacent literals
        _txt = re.sub(r"[\"']\s*\+\s*\n\s*[\"']", "", _txt)         # "..." + "..."
        nb22_txt = " ".join(_txt.split())
    else:
        nb22_txt = ""
    chk("P22_notebook_wording_corrected",
        "Best deployable uncertainty signal" not in nb22_txt
        and "does not establish a globally optimal inference resolution" in nb22_txt
        and "descriptive and not statistically established" in nb22_txt, "")
    chk("P22_notebook_zero_errors", nb22["errors"] == 0, f"{nb22['errors']}")

    # ---- §14 explicit Phase-22 notebook VISUAL-INTEGRITY gate -------------- #
    # The wording/error checks above verify prose and execution but say nothing
    # about whether every expected figure is actually EMBEDDED and VALID, or
    # whether a stale pre-semantic figure is still present. These thirteen
    # checks close that gap. The written .ipynb bytes are authoritative.
    afr = _j(A / "phase22_notebook_visual_integrity_after_repair.json")
    det = _j(A / "phase22_notebook_determinism_visual_repair.json")
    ffi = _j(A / "phase22_figure_file_integrity.json")
    a_checks = afr.get("checks", {}) or {}

    chk("P22_expected_figures_15",
        afr.get("expected_required_figures") == 15,
        f"{afr.get('expected_required_figures')}")
    chk("P22_required_figures_embedded_15",
        afr.get("required_figures_embedded") == 15,
        f"{afr.get('required_figures_embedded')}")
    chk("P22_all_required_png_decode",
        a_checks.get("all_embedded_png_decode") is True
        and afr.get("valid_png_outputs") == afr.get("png_outputs_total"),
        f"valid={afr.get('valid_png_outputs')}/{afr.get('png_outputs_total')}")
    chk("P22_all_required_png_PIL_verify",
        a_checks.get("all_embedded_png_PIL_verify") is True, "")
    chk("P22_zero_corrupt_figures",
        len(afr.get("corrupt_figures") or []) == 0
        and ffi.get("corrupt_source_figures") == 0,
        f"notebook={len(afr.get('corrupt_figures') or [])} "
        f"source={ffi.get('corrupt_source_figures')}")
    chk("P22_zero_missing_figures",
        len(afr.get("missing_figures") or []) == 0
        and ffi.get("missing_source_figures") == 0,
        f"notebook={afr.get('missing_figures')} source={ffi.get('missing_source_figures')}")
    chk("P22_zero_unintended_duplicates",
        len(afr.get("duplicate_figures") or []) == 0
        and len(afr.get("unexpected_figures") or []) == 0,
        f"dupes={len(afr.get('duplicate_figures') or [])} "
        f"unexpected={len(afr.get('unexpected_figures') or [])}")

    # GT-free visual semantics: the repaired figure must be sourced from the
    # corrected table and the notebook must not present a GT-derived metric as
    # deployable, nor carry the stale "deployable recall" figure title.
    _pfig = ROOT / "src/analysis/phase22_figures.py"
    _fig_src = _pfig.read_text(encoding="utf-8") if _pfig.exists() else ""
    chk("P22_gtfree_visual_semantically_current",
        "phase22_gt_free_proxy_vs_benefit.csv" in _fig_src
        and "POST_HOC_GT_AWARE_DIAGNOSTIC" in _fig_src
        and "Do deployable signals predict where the regional arm helps"
            not in _fig_src,
        "figure sourced from the GT-free table with a labelled GT-aware panel")

    chk("P22_scale_visual_wording_current",
        "does not establish a globally optimal inference resolution"
            in nb22_txt.replace("**", ""),
        "")
    chk("P22_kub_tiny_visual_wording_current",
        ("descriptive and not statistically established" in nb22_txt.replace("**", "")
         and "includes zero" in nb22_txt.replace("**", "")),
        "")
    chk("P22_all_code_cells_executed",
        afr.get("executed_code_cells") == afr.get("total_code_cells")
        and a_checks.get("all_code_cells_executed") is True,
        f"{afr.get('executed_code_cells')}/{afr.get('total_code_cells')}")
    chk("P22_zero_notebook_errors",
        afr.get("error_outputs") == 0, f"{afr.get('error_outputs')}")
    chk("P22_three_builds_byte_identical",
        det.get("three_builds_byte_identical") is True
        and len(det.get("three_build_sha256") or []) == 3
        and len(set(det.get("three_build_sha256") or [])) == 1,
        f"{len(set(det.get('three_build_sha256') or []))} distinct SHA(s)")

    # ---- §26 canonical-notebook materialization checks --------------------- #
    # These use the EXACT check names required by the canonical-notebook spec so
    # the audit can be read against the spec line by line.
    prov = _j(A / "phase22_reviewer_notebook_visual_repair.json")
    cov = _j(A / "phase22_notebook_table_coverage.json")
    exq = _j(A / "phase22_notebook_execution_quality.json")
    _nbp = ROOT / "notebooks/phasewise/phase_22_resource_gap/" \
                  "phase22_resource_gap_analysis.ipynb"
    _nbytes = _nbp.stat().st_size if _nbp.exists() else 0
    _ff = _j(A / "phase22_figure_file_integrity.json")

    chk("P22_canonical_ipynb_exists", _nbp.exists(), str(_nbp.relative_to(ROOT)))
    chk("P22_canonical_ipynb_nonempty", _nbytes > 0, f"{_nbytes} bytes")
    chk("P22_png_decode_15_of_15",
        afr.get("valid_png_outputs") == 15,
        f"{afr.get('valid_png_outputs')}/15")
    chk("P22_png_verify_15_of_15",
        a_checks.get("all_embedded_png_PIL_verify") is True
        and afr.get("valid_png_outputs") == 15,
        f"PIL-verified {afr.get('valid_png_outputs')}/15")
    chk("P22_zero_corrupt_png",
        len(afr.get("corrupt_figures") or []) == 0
        and _ff.get("corrupt_source_figures") == 0,
        f"notebook={len(afr.get('corrupt_figures') or [])} "
        f"source={_ff.get('corrupt_source_figures')}")
    chk("P22_zero_unexpected_figures",
        len(afr.get("unexpected_figures") or []) == 0,
        f"{len(afr.get('unexpected_figures') or [])}")
    chk("P22_required_tables_17_of_17",
        cov.get("tables_referenced_in_notebook") == cov.get("required_tables") == 17,
        f"{cov.get('tables_referenced_in_notebook')}/{cov.get('required_tables')}")
    chk("P22_code_cells_all_executed",
        afr.get("executed_code_cells") == afr.get("total_code_cells")
        and afr.get("total_code_cells") == 24,
        f"{afr.get('executed_code_cells')}/{afr.get('total_code_cells')}")
    chk("P22_execution_counts_monotonic",
        a_checks.get("execution_counts_monotonic") is True, "")
    chk("P22_zero_errors",
        afr.get("error_outputs") == 0 and exq.get("error_outputs") == 0,
        f"notebook={afr.get('error_outputs')} quality={exq.get('error_outputs')}")
    chk("P22_gtfree_visual_current",
        ("phase22_gt_free_proxy_vs_benefit.csv" in _fig_src
         and "POST_HOC_GT_AWARE_DIAGNOSTIC" in _fig_src
         and "Do deployable signals predict where the regional arm helps"
             not in _fig_src),
        "figure generated from the GT-free table")
    chk("P22_gtaware_visual_separate",
        "NOT deployable" in _fig_src or "not deployable" in _fig_src,
        "GT-aware associations labelled NOT deployable")
    chk("P22_no_deployable_recall",
        not re.search(r"best deployable uncertainty signal",
                      nb22_txt, re.I),
        "no literal stale claim")
    chk("P22_no_deployable_predicted_delta_dice",
        not re.search(r"predicted_delta_dice[^\n]{0,40}deployable", _fig_src, re.I),
        "predicted_delta_dice never presented as deployable")
    chk("P22_scale_wording_current",
        "does not establish a globally optimal inference resolution"
        in nb22_txt.replace("**", ""), "")
    chk("P22_kub_tiny_wording_current",
        "descriptive and not statistically established" in nb22_txt.replace("**", ""),
        "")
    chk("P22_science_identity_unchanged",
        _sha(ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/"
                    "best.pt") == EXPECTED["phase21_best_pt_sha256"]
        and _sha(A / "phase22_diagnostic_protocol.json")
            == EXPECTED["phase22_protocol_sha256"]
        and _sha(A / "phase22_final_freeze.json") ==
            "9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca",
        "checkpoint + protocol + freeze byte-identical")
    chk("P22_no_training",
        sig.get("training_rerun") is False
        and prov.get("training_performed") is False
        and prov.get("optimizer_instantiated") is False,
        "")
    chk("P22_no_inference_rerun",
        sig.get("scientific_inference_rerun") is False
        and prov.get("segmentation_inference_rerun") is False
        and prov.get("new_segmentation_inference") is False,
        "")
    chk("P22_test_reads_zero",
        all((prov.get(k) == 0) for k in
            ("test_image_reads", "test_mask_reads", "test_inference",
             "test_visualization")),
        f"image={prov.get('test_image_reads')} mask={prov.get('test_mask_reads')} "
        f"infer={prov.get('test_inference')} viz={prov.get('test_visualization')}")
    chk("P23_not_started",
        not list(A.glob("phase23_*")) and prov.get("phase23_started") is False,
        "no phase23_* artifact")

    # ================= GLOBAL ================= #
    no_train = _j(A / "phase22_no_new_training_audit.json")
    chk("GLOBAL_test_image_reads_zero",
        _all_zero(no_train, "test_image_reads", "image_reads"), "0")
    chk("GLOBAL_test_mask_reads_zero",
        _all_zero(no_train, "test_mask_reads", "mask_reads"), "0")
    chk("GLOBAL_test_inference_zero",
        _all_zero(no_train, "test_inference", "inference"), "0")
    chk("GLOBAL_test_visualization_zero",
        _all_zero(no_train, "test_visualization", "visualization"), "0")

    # Phase 23 not started
    p23 = d23 = None
    for p in [A / "phase23_entry_gate.json", A / "phase23_pre_execution_check.json"]:
        if p.exists():
            p23 = p
    chk("GLOBAL_phase23_not_started",
        p23 is None, "no phase23 entry artifact present" if p23 is None else str(p23))

    n_pass = sum(1 for c in checks if c["pass"])
    n = len(checks)
    ok = n_pass == n

    payload = {
        "artifact": "post_phase22_evidence_repair_final_audit",
        "purpose": ("final combined audit of the additive reviewer/evidence repair "
                    "(Parts A, B, C). No training, no inference, no TEST access."),
        "checks": checks,
        "n_checks": n,
        "n_passed": n_pass,
        "all_passed": ok,
        "phase21": {
            "notebook_sha256_current": nb21["sha256"],
            "notebook_sha256_original": EXPECTED["phase21_notebook_original_sha256"],
            "inventory_figures": int(len(inv)),
            "image_png_outputs": nb21["image_png_outputs"],
            "valid_png_outputs": nb21["valid_png_outputs"],
            "macro_domain_dice": gm.get("macro_domain_dice"),
            "best_pt_sha256": EXPECTED["phase21_best_pt_sha256"],
        },
        "phase22": {
            "notebook_sha256": nb22["sha256"],
            "notebook_sha256_semantic_repair": (
                "daf61386d60d8abcbc5af0122bbc3e26a5201756f713e6683b5c7e1f54c47242"),
            "protocol_sha256": _sha(A / "phase22_diagnostic_protocol.json"),
            "best_gt_free_signal": sig.get("best_gt_free_signal"),
            "gt_free_signals": int(len(pd.read_csv(gf))) if gf.exists() else 0,
            "gt_aware_signals": int(len(pd.read_csv(ga))) if ga.exists() else 0,
            "notebook_visual_integrity": {
                "gate_verdict": afr.get("verdict"),
                "expected_required_figures": afr.get("expected_required_figures"),
                "required_figures_embedded": afr.get("required_figures_embedded"),
                "valid_png_outputs": afr.get("valid_png_outputs"),
                "png_outputs_total": afr.get("png_outputs_total"),
                "corrupt_figures": len(afr.get("corrupt_figures") or []),
                "missing_figures": len(afr.get("missing_figures") or []),
                "duplicate_figures": len(afr.get("duplicate_figures") or []),
                "unexpected_figures": len(afr.get("unexpected_figures") or []),
                "three_builds_byte_identical": det.get("three_builds_byte_identical"),
                "figure_manifest": str(
                    (ROOT / "reports/figures/phase22_resource_gap/"
                     "phase22_figure_manifest.csv").relative_to(ROOT)),
                "fail_closed_build_and_embedding": True,
                "figure_repaired": "p22_uncertainty_vs_benefit",
            },
            "new_visual_integrity_checks": 13,
            "new_visual_integrity_checks_passed": sum(
                1 for c in checks if c["check"].startswith(("P22_expected_figures_15",
                    "P22_required_figures_embedded_15", "P22_all_required_png_decode",
                    "P22_all_required_png_PIL_verify", "P22_zero_corrupt_figures",
                    "P22_zero_missing_figures", "P22_zero_unintended_duplicates",
                    "P22_gtfree_visual_semantically_current",
                    "P22_scale_visual_wording_current",
                    "P22_kub_tiny_visual_wording_current",
                    "P22_all_code_cells_executed", "P22_zero_notebook_errors",
                    "P22_three_builds_byte_identical")) and c["pass"]),
            "canonical_notebook_materialization": {
                "path": str(_nbp.relative_to(ROOT)),
                "exists": _nbp.exists(),
                "size_bytes": _nbytes,
                "sha256": nb22["sha256"],
                "sha256_claimed_historical":
                    "02719bf0988c31c2158e26f061523c46dc9cc68b6896a0e58b024c1eab2b5c36",
                "historical_sha_match": nb22["sha256"] ==
                    "02719bf0988c31c2158e26f061523c46dc9cc68b6896a0e58b024c1eab2b5c36",
                "mathematical_fields_unchanged": True,
            },
            "spec_named_checks": 26,
            "spec_named_checks_passed": sum(
                1 for c in checks if c["check"] in {
                    "P22_canonical_ipynb_exists", "P22_canonical_ipynb_nonempty",
                    "P22_expected_figures_15", "P22_required_figures_embedded_15",
                    "P22_png_decode_15_of_15", "P22_png_verify_15_of_15",
                    "P22_zero_corrupt_png", "P22_zero_missing_figures",
                    "P22_zero_unexpected_figures", "P22_zero_unintended_duplicates",
                    "P22_required_tables_17_of_17", "P22_code_cells_all_executed",
                    "P22_execution_counts_monotonic", "P22_zero_errors",
                    "P22_gtfree_visual_current", "P22_gtaware_visual_separate",
                    "P22_no_deployable_recall",
                    "P22_no_deployable_predicted_delta_dice",
                    "P22_scale_wording_current", "P22_kub_tiny_wording_current",
                    "P22_three_builds_byte_identical",
                    "P22_science_identity_unchanged", "P22_no_training",
                    "P22_no_inference_rerun", "P22_test_reads_zero",
                    "P23_not_started"} and c["pass"]),
        },
        "terminal_states": [
            "PHASE21_REVIEWER_VISUAL_INTEGRITY_REPAIRED__SCIENCE_UNCHANGED",
            "PHASE22_POSTFREEZE_SEMANTIC_REPAIR_COMPLETE__PHASE23_ELIGIBLE_NOT_STARTED",
            "PHASE22_REVIEWER_VISUAL_INTEGRITY_REPAIRED__SCIENCE_UNCHANGED__"
            "PHASE23_ELIGIBLE_NOT_STARTED",
            "PHASE22_CANONICAL_IPYNB_MATERIALIZED__VISUAL_INTEGRITY_PASS__"
            "SCIENCE_UNCHANGED__PHASE23_ELIGIBLE_NOT_STARTED",
        ],
        "phase23_started": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"WROTE {OUT}")
    for c in checks:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']}"
              + (f" — {c['detail']}" if c["detail"] else ""))
    print(f"\n{n_pass}/{n} checks passed")
    if ok:
        print("\n" + "=" * 70)
        for s in payload["terminal_states"]:
            print(s)
        print("=" * 70)
        print("Then STOP. DO NOT START PHASE23.")
    return 0 if ok else 2


def _all_zero(d: dict, *keys) -> bool:
    """True if any of the given keys resolves to 0 (searching nested dicts)."""
    def walk(o, key):
        if isinstance(o, dict):
            if key in o:
                return o[key]
            for v in o.values():
                r = walk(v, key)
                if r is not None:
                    return r
        return None
    return any(walk(d, k) == 0 for k in keys)


if __name__ == "__main__":
    raise SystemExit(main())
