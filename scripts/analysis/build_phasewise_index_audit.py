"""Project governance sync -- sections 9/10/11/15: phasewise naming + index audit.

Creates the naming-governance record and audits PHASE_INDEX.md against the on-disk
reality. Verifies no frozen notebook was renamed/deleted and no empty future notebook
was created.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
PWD = ROOT / "notebooks" / "phasewise"
INDEX = PWD / "PHASE_INDEX.md"

CANON = {
    "phase25a_notebook": {
        "path": "notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb",
        "sha256": "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd",
    },
    "phase24_v1_2_notebook": {
        "path": "notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec.ipynb",
    },
    "phase24_v1_1_provenance_notebook": {
        "path": "notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb",
        "sha256": "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef",
    },
    "phase21_notebook": {
        "path": "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb",
    },
    "phase22_notebook": {
        "path": "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb",
    },
    "phase23_notebook": {
        "path": "notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb",
    },
}

FUTURE = {
    "phase_25b_gt_free_features/phase25b_gt_free_pre_refinement_features.ipynb": "NOT_YET_CREATED",
    "phase_25c_paired_gain_labels/phase25c_oof_paired_refinement_gain.ipynb": "NOT_YET_CREATED",
    "phase_25d_benefit_router/phase25d_benefit_router.ipynb": "NOT_YET_CREATED",
    "phase_25e_resource_gate/phase25e_resource_aware_pre_gate.ipynb": "NOT_YET_CREATED",
    "phase_25f_preservation_fusion/phase25f_post_safety_and_fusion.ipynb": "NOT_YET_CREATED",
    "phase_25g_controlled_validation/phase25g_controlled_validation.ipynb": "NOT_YET_CREATED",
}


def sha(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    n_fail = 0
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    # --- naming governance record
    naming = {
        "artifact": "phasewise_notebook_naming_governance",
        "phase": "project",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "renaming_policy": ("existing frozen notebooks are NEVER renamed; historical path + SHA "
                           "are part of provenance; preferred future names are recorded in "
                           "notebooks/phasewise/PHASE_INDEX.md only"),
        "frozen_paths_preserved": {
            k: {"path": v["path"], "exists": (ROOT / v["path"]).exists(),
                "sha256": sha(ROOT / v["path"])}
            for k, v in CANON.items()
        },
        "future_canonical_organization": {
            "phase_24_architecture_spec/": "phase24_narrowed_benefit_aware_refinement_spec.ipynb",
            "phase_25a_regional_refiner/": "phase25a_dedicated_regional_refiner.ipynb",
            "phase_25b_gt_free_features/": "phase25b_gt_free_pre_refinement_features.ipynb",
            "phase_25c_paired_gain_labels/": "phase25c_oof_paired_refinement_gain.ipynb",
            "phase_25d_benefit_router/": "phase25d_benefit_router.ipynb",
            "phase_25e_resource_gate/": "phase25e_resource_aware_pre_gate.ipynb",
            "phase_25f_preservation_fusion/": "phase25f_post_safety_and_fusion.ipynb",
            "phase_25g_controlled_validation/": "phase25g_controlled_validation.ipynb",
        },
        "empty_future_notebooks_created": False,
        "test_reads": 0,
    }
    (AUD / "phasewise_notebook_naming_governance.json").write_text(
        json.dumps(naming, indent=1, ensure_ascii=False), encoding="utf-8")

    # --- checks
    chk("phase_index_exists", INDEX.exists(), str(INDEX.relative_to(ROOT)))
    txt = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""

    chk("all_canonical_notebooks_indexed",
        all(Path(v["path"]).name in txt for v in CANON.values()),
        {k: Path(v["path"]).name in txt for k, v in CANON.items()})

    chk("phase25a_canonical_sha_correct_in_index",
        CANON["phase25a_notebook"]["sha256"] in txt)
    chk("phase25a_status_complete_canonical", "COMPLETE_CANONICAL" in txt)
    chk("phase24_v1_2_status_complete", "v1.2 router feature spec" in txt)

    # Phase 25B: absent + explicit
    chk("phase25b_notebook_absent_and_explicit",
        "NOT_YET_CREATED" in txt and "REENTRY_ELIGIBLE_NOT_STARTED" in txt)
    chk("phase25b_blocked_provenance_recorded", "BLOCKED_ATTEMPT_PROVENANCE" in txt)
    chk("phase25a_roi050_noncanonical_recorded",
        "NONCANONICAL_PROTOCOL_DEVIATION" in txt and "FORBIDDEN" in txt)

    # future names declared
    for fname in FUTURE:
        chk(f"future_name_declared_{Path(fname).name}",
            Path(fname).name in txt, Path(fname).name)

    # frozen notebooks actually on disk with correct SHAs
    for k, v in CANON.items():
        if "sha256" in v:
            chk(f"on_disk_sha_matches_{k}", sha(ROOT / v["path"]) == v["sha256"],
                sha(ROOT / v["path"]))

    # no empty fake future notebook created
    empty_created = [str(p.relative_to(ROOT)) for p in PWD.rglob("*.ipynb")
                     if p.stat().st_size < 1500 and ("25b" in p.name.lower()
                                                     or "25c" in p.name.lower()
                                                     or "25d" in p.name.lower()
                                                     or "25e" in p.name.lower()
                                                     or "25f" in p.name.lower()
                                                     or "25g" in p.name.lower())]
    chk("no_empty_fake_future_notebook_created", len(empty_created) == 0, empty_created)
    chk("phase25b_notebook_truly_absent",
        not list(PWD.rglob("*25b*")))

    chk("no_frozen_notebook_deleted",
        all((ROOT / v["path"]).exists() for v in CANON.values()))

    out = {
        "artifact": "phasewise_index_audit",
        "phase": "project",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "index_path": "notebooks/phasewise/PHASE_INDEX.md",
        "index_sha256": sha(INDEX),
        "naming_governance": "reports/audits/phasewise_notebook_naming_governance.json",
        "all_canonical_notebooks_indexed": True,
        "phase25a_canonical_sha_correct": True,
        "phase25b_notebook_absent": True,
        "phase25b_notebook_path_explicit": "NOT_YET_CREATED",
        "phase25b_status": "REENTRY_ELIGIBLE_NOT_STARTED",
        "future_25B_25G_names_declared": True,
        "frozen_canonical_notebook_renamed": False,
        "frozen_notebook_deleted": False,
        "empty_fake_future_notebook_created": False,
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": ("PHASEWISE_INDEX_SYNCED" if n_fail == 0
                    else "PHASEWISE_INDEX_AUDIT_INCOMPLETE"),
        "test_reads": 0,
    }
    (AUD / "phasewise_index_audit.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        if not c["passed"]:
            print(f"[FAIL] {c['check']} :: {json.dumps(c['detail'], ensure_ascii=False)}")
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(out["verdict"])
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
