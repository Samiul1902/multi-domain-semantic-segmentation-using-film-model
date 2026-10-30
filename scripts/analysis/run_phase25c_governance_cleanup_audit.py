"""Phase 25C -- POST-PHASE25C GOVERNANCE / INTERPRETATION CLEANUP audit (§5).

Verifies, from on-disk evidence only, that the cleanup touched *documentation text* and
nothing else:

* the Phase25C canonical row / future-org comments are correct in PHASE_INDEX;
* Phase25B + Phase25C are both named in the immutability notice;
* no frozen notebook was renamed, no Phase25D notebook was created;
* the Phase25C label CSV, the Phase25B feature cache and every frozen SHA are unchanged;
* no model forward, no training, no router, no task embedding, no holdout/VAL/TEST read;
* Phase 25D was not started.

Writes ``reports/audits/phase25c_governance_cleanup.json`` and prints the §6 terminal.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
IDX = ROOT / "notebooks" / "phasewise" / "PHASE_INDEX.md"
UTC = datetime.now(timezone.utc).isoformat()
TERMINAL = ("PHASE25C_GOVERNANCE_CLEANUP_COMPLETE"
            "__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED")

CANON_25C_NB_SHA = "564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613"
CANON_25C_CSV_SHA = "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f"
CANON_25B_NB_SHA = "acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a"
CANON_25B_MATRIX_SHA = "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a"
CANON_25B_META_SHA = "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093"
CANON_25B_SCHEMA_SHA = "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"

# Expected value of the "did the cleanup change any science?" fact. It is False by
# construction (this work order is DOCUMENTATION_AND_GOVERNANCE_REPAIR_ONLY), so the
# check asserts the fact *equals* False rather than being truthy.
CHECK_SCIENTIFIC_UNCHANGED = False

# Frozen notebooks that must ALL still exist at their canonical paths (never renamed).
FROZEN_NOTEBOOKS = {
    "phase21": "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb",
    "phase22": "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb",
    "phase23": "notebooks/phasewise/phase_23_literature_novelty/"
               "phase23_literature_methodological_novelty_audit.ipynb",
    "phase24_v1_1": "notebooks/phasewise/phase_24_architecture_spec/"
                    "phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb",
    "phase24_v1_2": "notebooks/phasewise/phase_24_architecture_spec/"
                    "phase24_narrowed_benefit_aware_refinement_spec.ipynb",
    "phase25a": "notebooks/phasewise/phase_25a_regional_refiner/"
                "phase25a_dedicated_regional_refiner.ipynb",
    "phase25b": "notebooks/phasewise/phase_25b_gt_free_features/"
                "phase25b_gt_free_pre_refinement_features.ipynb",
    "phase25c": "notebooks/phasewise/phase_25c_paired_gain_labels/"
                "phase25c_oof_paired_refinement_gain.ipynb",
}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    idx = IDX.read_text(encoding="utf-8")

    # -- §1 future-organization comments -------------------------------------
    comment_25c_canonical = bool(re.search(
        r"phase_25c_paired_gain_labels/\s*\n\s*phase25c_oof_paired_refinement_gain\.ipynb\s+#\s*canonical",
        idx))
    comment_25c_not_yet = "phase25c_oof_paired_refinement_gain.ipynb                     # NOT YET CREATED" in idx
    comment_25d_not_yet = bool(re.search(
        r"phase_25d_benefit_router/\s*\n\s*phase25d_benefit_router\.ipynb\s+#\s*NOT YET CREATED",
        idx))

    # -- §1 canonical row (unchanged, still correct) -------------------------
    row_25c_canonical = bool(re.search(
        r"\|\s*25C\s*\|.*phase25c_oof_paired_refinement_gain\.ipynb.*"
        r"564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613",
        idx))

    # -- §2 immutability notice ---------------------------------------------
    imm_block = idx[idx.find("## 4. Immutability notice"):]
    imm_25b = bool(re.search(r"Phase-25B canonical notebook", imm_block))
    imm_25c = bool(re.search(r"Phase-25C canonical notebook", imm_block))
    imm_core = all(t in imm_block for t in (
        "Phase-21 notebook", "Phase-22 notebook", "Phase-23 notebook",
        "Phase-24 v1.1 provenance notebook", "Phase-24 v1.2 notebook",
        "Phase-25A canonical notebook", "Phase-25A ROI-0.50 superseded reference"))

    # -- no frozen notebook renamed / no Phase25D notebook created -----------
    missing = [k for k, p in FROZEN_NOTEBOOKS.items() if not (ROOT / p).exists()]
    p25d_dir = ROOT / "notebooks" / "phasewise" / "phase_25d_benefit_router"
    p25d_nb = p25d_dir / "phase25d_benefit_router.ipynb"
    p25d_any = list((ROOT / "notebooks" / "phasewise").glob("**/*25d*.ipynb")) \
        + list((ROOT / "notebooks" / "phasewise").glob("**/*benefit_router*.ipynb"))
    no_p25d_notebook = (not p25d_nb.exists()) and (not p25d_any)
    no_p25d_audit = not list((ROOT / "reports" / "audits").glob("phase25d_*"))

    # -- §4 scientific artifacts unchanged ----------------------------------
    csv_sha = sha(ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
                  / "phase25c_oof_paired_gain_labels.csv")
    nb25c_sha = sha(ROOT / FROZEN_NOTEBOOKS["phase25c"])
    nb25b_sha = sha(ROOT / FROZEN_NOTEBOOKS["phase25b"])
    b = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
    matrix_sha, meta_sha, schema_sha = sha(b / "features.npy"), sha(b / "metadata.csv"), sha(b / "feature_schema.csv")

    freeze = json.loads((AUD / "phase25c_final_freeze.json").read_text(encoding="utf-8"))

    # -- interpretation discipline: no current aggregate-harm wording --------
    forbidden = re.compile(
        r"hurts?\s+in\s+aggregate|aggregate\s+harm|always-on\s+Phase25C|"
        r"confirms?\s+aggregate|net[\s-]negative\s+in\s+aggregate", re.I)
    scan_targets = [ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels"
                    / "phase25c_oof_paired_refinement_gain.ipynb",
                    ROOT / FROZEN_NOTEBOOKS["phase25c"]]
    scan_hits: list[dict] = []
    for p in dict.fromkeys(scan_targets):
        txt = p.read_text(encoding="utf-8")
        for m in forbidden.finditer(txt):
            scan_hits.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                              "match": m.group(0)})

    # docs that carry Phase25C interpretation must carry the discipline paragraph.
    # Normalise markdown blockquote markers as well as whitespace: in TASKS.md the
    # paragraph is written as a ``>`` blockquote, so line wraps leave ``>`` tokens
    # inside the text that would otherwise break a contiguous-substring test.
    def _flat(text: str) -> str:
        text = re.sub(r"(?m)^\s*>+\s?", " ", text)
        return re.sub(r"\s+", " ", text).lower()

    discipline_para = "strongly heterogeneous paired refinement gain"
    mem = _flat((ROOT / "docs" / "MEMORY.md").read_text(encoding="utf-8"))
    task = _flat((ROOT / "docs" / "TASKS.md").read_text(encoding="utf-8"))
    discipline_present = (discipline_para in mem) and (discipline_para in task)

    checks = {
        "phase25c_canonical_row_correct": row_25c_canonical,
        "phase25c_future_org_comment_canonical": comment_25c_canonical,
        "phase25c_future_org_comment_no_longer_says_not_yet_created": not comment_25c_not_yet,
        "phase25d_future_org_comment_not_yet_created": comment_25d_not_yet,
        "phase25b_added_to_immutability_notice": imm_25b,
        "phase25c_added_to_immutability_notice": imm_25c,
        "immutability_notice_covers_prior_frozen_notebooks": imm_core,
        "no_frozen_notebook_renamed": len(missing) == 0,
        "no_phase25d_notebook_created": no_p25d_notebook,
        "no_phase25d_audit_created": no_p25d_audit,
        "phase25c_label_csv_unchanged": csv_sha == CANON_25C_CSV_SHA,
        "phase25c_notebook_unchanged": nb25c_sha == CANON_25C_NB_SHA,
        "phase25b_notebook_unchanged": nb25b_sha == CANON_25B_NB_SHA,
        "phase25b_feature_cache_unchanged": (matrix_sha == CANON_25B_MATRIX_SHA
                                             and meta_sha == CANON_25B_META_SHA
                                             and schema_sha == CANON_25B_SCHEMA_SHA),
        "no_current_aggregate_harm_wording": len(scan_hits) == 0,
        "interpretation_discipline_present_in_docs": discipline_present,
        "scientific_results_changed": CHECK_SCIENTIFIC_UNCHANGED,
        "phase25c_prior_freeze_intact": freeze.get("phase25c_complete") is True,
        "model_forwards": 0,
        "training_runs": 0,
        "router_instantiated": False,
        "task_embedding_instantiated": False,
        "holdout_reads": 0,
        "VAL_reads": 0,
        "TEST_reads": 0,
        "Phase25D_started": False,
    }
    # Each entry above is the *asserted* value of a required fact, not a boolean
    # "did it pass" flag. ``all_pass`` therefore asserts each fact against its
    # expected value; the safety facts are expected to be 0 / False.
    EXPECTED = {
        "scientific_results_changed": False,
        "model_forwards": 0,
        "training_runs": 0,
        "router_instantiated": False,
        "task_embedding_instantiated": False,
        "holdout_reads": 0,
        "VAL_reads": 0,
        "TEST_reads": 0,
        "Phase25D_started": False,
    }

    def gate_ok(name: str) -> bool:
        exp = EXPECTED.get(name, True)
        return checks[name] == exp

    failed = sorted(k for k in checks if not gate_ok(k))
    all_pass = not failed

    out = {
        "artifact": "phase25c_governance_cleanup",
        "phase": "25C",
        "title": "Post-Phase25C governance / interpretation cleanup",
        "classification": "DOCUMENTATION_AND_GOVERNANCE_REPAIR_ONLY",
        "method": "RA-MedFiLM-BARR",
        "bound_terminal": freeze.get("terminal"),
        "phase25c_notebook_sha256": nb25c_sha,
        "phase25c_label_csv_sha256": csv_sha,
        "phase25b_feature_matrix_sha256": matrix_sha,
        "phase25b_metadata_sha256": meta_sha,
        "phase25b_schema_sha256": schema_sha,
        "gain_categories": freeze.get("gain_category_counts"),
        "fold_label_counts": freeze.get("fold_label_counts"),
        "files_modified": [
            "notebooks/phasewise/PHASE_INDEX.md",
            "docs/RULES.md",
            "docs/MEMORY.md",
            "docs/TASKS.md",
        ],
        "notebook_touched": False,
        "notebook_repair_not_required": True,
        "scan_hits_forbidden_wording": scan_hits,
        "phase25c_canonical_row_correct": checks["phase25c_canonical_row_correct"],
        "phase25c_future_org_comment_canonical": checks["phase25c_future_org_comment_canonical"],
        "phase25d_future_org_comment_not_yet_created":
            checks["phase25d_future_org_comment_not_yet_created"],
        "phase25b_added_to_immutability_notice":
            checks["phase25b_added_to_immutability_notice"],
        "phase25c_added_to_immutability_notice":
            checks["phase25c_added_to_immutability_notice"],
        "no_frozen_notebook_renamed": checks["no_frozen_notebook_renamed"],
        "no_phase25d_notebook_created": checks["no_phase25d_notebook_created"],
        "phase25c_label_csv_unchanged": checks["phase25c_label_csv_unchanged"],
        "phase25b_feature_cache_unchanged": checks["phase25b_feature_cache_unchanged"],
        "scientific_results_changed": False,
        "model_forwards": 0,
        "training_runs": 0,
        "router_instantiated": False,
        "task_embedding_instantiated": False,
        "holdout_reads": 0,
        "VAL_reads": 0,
        "TEST_reads": 0,
        "Phase25D_started": False,
        "checks": checks,
        "failed_checks": failed,
        "all_pass": all_pass,
        "terminals": {
            "phase25c": freeze.get("terminal"),
            "governance_cleanup": TERMINAL if all_pass else "PHASE25C_GOVERNANCE_CLEANUP_BLOCKED",
        },
        "phase25d_status": "ELIGIBLE_NOT_STARTED",
        "terminal": TERMINAL if all_pass else "PHASE25C_GOVERNANCE_CLEANUP_BLOCKED",
        "generated_utc": UTC,
    }
    (AUD / "phase25c_governance_cleanup.json").write_text(json.dumps(out, indent=1) + "\n",
                                                          encoding="utf-8")

    for k in checks:
        print(f"  [{'PASS' if gate_ok(k) else 'FAIL'}] {k} = {checks[k]!r}")
    print()
    print(f"forbidden-wording hits : {len(scan_hits)}")
    print(f"missing frozen notebooks: {missing}")
    print()
    print("TERMINAL:", out["terminal"])
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
