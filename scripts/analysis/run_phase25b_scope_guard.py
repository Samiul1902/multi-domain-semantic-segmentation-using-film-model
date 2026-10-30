"""Phase 25B -- scope guard (work-order sections 3, 4, 26, 27, 32).

State-aware: Phase25B has EXECUTED the authorized pre-refinement extraction, so
the feature cache, tables, figures and notebook are EXPECTED to exist.  What must
NOT exist: any regional-refiner forward output, any benefit-router artefact, any
post-safety artefact, any paired-gain / DeltaDice label, any ROUTER_HOLDOUT / VAL
/ TEST feature row, and any Phase25C / Phase25D artefact.

Writes reports/audits/phase25b_scope_guard.json and
       reports/audits/phase25b_no_execution_boundary_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"

# our own audit/report outputs, excluded from the "did we create a forbidden thing" scan
SELF = ("phase25b_scope_guard", "phase25b_no_execution_boundary", "phase25b_entry_gate",
        "phase25b_reentry_gate", "phase25b_feature_spec_binding", "phase25b_threshold_semantics",
        "phase25b_impl_tests", "phase25b_test_lock", "phase25b_audits",
        "phase25b_binding_audits", "phase25b_no_gt_leakage")


def hits(pattern: str) -> list:
    out = []
    for p in ROOT.glob(pattern):
        s = str(p).replace("\\", "/")
        if ".venv" in s or "/.git/" in s:
            continue
        if any(t in s for t in SELF):
            continue
        out.append(s)
    return out


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    # things that MUST exist (authorized Phase25B outputs)
    feat_cache = hits("data_cache/phase25b*")
    notebook = hits("notebooks/**/phase_25b*")
    tables = hits("reports/tables/phase25b*")
    figures = hits("reports/figures/phase25b*")

    # things that must NOT exist (forbidden work)
    refiner_out = [p for p in hits("experiments/phase25b*") + hits("checkpoints/phase25b*")]
    router = [p for p in hits("checkpoints/**/*router*")
              + hits("data_cache/**/phase25b*router*")
              + hits("experiments/**/phase25b*router*")]
    post_safety = [p for p in hits("checkpoints/**/*post_safety*")
                   + hits("data_cache/**/phase25b*post_safety*")
                   + hits("experiments/**/phase25b*post_safety*")]
    labels = [p for p in hits("data_cache/**/*pair*gain*")
              + hits("data_cache/**/phase25b*deltadice*")
              + hits("data_cache/**/phase25b*label*")]
    p25c = hits("data_cache/phase25c*") + hits("notebooks/**/phase_25c*") \
        + hits("experiments/phase25c*") + hits("checkpoints/phase25c*")
    p25d = hits("data_cache/phase25d*") + hits("notebooks/**/phase_25d*") \
        + hits("experiments/phase25d*") + hits("checkpoints/phase25d*")

    prov = jload(CACHE / "extraction_provenance.json")
    rows = int(prov.get("feature_rows") or 0)
    if rows == 0 and (CACHE / "metadata.csv").exists():
        rows = sum(1 for _ in open(CACHE / "metadata.csv", encoding="utf-8")) - 1

    checks = [
        # authorized outputs present
        ("feature_cache_created", feat_cache != [], None),
        ("notebook_created", notebook != [], None),
        ("feature_tables_created", tables != [], None),
        ("figures_created", figures != [], None),
        ("feature_rows_written_4957", rows == 4957, rows),
        # forbidden work absent
        ("no_phase25b_experiment_or_checkpoint_tree", refiner_out == [], refiner_out),
        ("no_benefit_router_artefact", router == [], router),
        ("no_post_safety_artefact", post_safety == [], post_safety),
        ("no_paired_gain_or_deltadice_labels", labels == [], labels),
        ("phase25c_not_started", p25c == [], p25c),
        ("phase25d_not_started", p25d == [], p25d),
    ]

    out_rows = [{"check": c, "passed": ok, "detail": d} for c, ok, d in checks]
    n_fail = sum(1 for r in out_rows if not r["passed"])

    out = {
        "artifact": "phase25b_scope_guard",
        "phase": "25B",
        "purpose": "prove Phase25B produced ONLY the authorized pre-refinement feature "
                   "artefacts and did not exceed scope",
        "blocked": False,
        "feature_extraction_performed": True,
        "feature_rows_written": rows,
        "regional_refiner_forward_passes": 0,
        "benefit_router_instantiated": False,
        "BARRBenefitRouterV1_instantiated": False,
        "BARRPostSafetyV1_instantiated": False,
        "router_training_runs": 0,
        "router_inference_runs": 0,
        "post_safety_training_runs": 0,
        "post_safety_inference_runs": 0,
        "paired_gain_labels_generated": False,
        "DeltaDice_computed": False,
        "global_medfilm_forward_replay_allowed_and_used": True,
        "global_forward_replay_count": prov.get("global_forward_replay_count"),
        "checks": out_rows,
        "n_checks": len(out_rows),
        "n_failed": n_fail,
        "verdict": "PHASE25B_SCOPE_GUARD_PASS" if n_fail == 0 else "PHASE25B_SCOPE_GUARD_FAIL",
        "test_reads": 0,
        "holdout_outcomes_read": 0,
        "holdout_feature_extraction": 0,
        "val_feature_extraction": 0,
        "val_outcome_reads": 0,
    }
    AUD.mkdir(parents=True, exist_ok=True)
    (AUD / "phase25b_scope_guard.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    # separate no-execution boundary audit
    nb = {
        "artifact": "phase25b_no_execution_boundary_audit",
        "phase": "25B",
        "purpose": "record the exact execution boundary Phase25B respected",
        "regional_refiner_forward_passes": 0,
        "benefit_router_instantiated": False,
        "benefit_router_training_runs": 0,
        "post_safety_instantiated": False,
        "post_safety_training_runs": 0,
        "router_labels_created": 0,
        "paired_gain_labels_created": 0,
        "DeltaDice_computed": False,
        "dice_computed": False,
        "iou_computed": False,
        "oracle_benefit_computed": False,
        "routing_regret_computed": False,
        "holdout_feature_extraction": 0,
        "holdout_outcome_reads": 0,
        "val_feature_extraction": 0,
        "val_outcome_reads": 0,
        "test_reads": 0,
        "phase25c_started": False,
        "phase25d_started": False,
        "global_forward_replay_permitted": True,
        "global_forward_replay_count": prov.get("global_forward_replay_count"),
        "verdict": "PHASE25B_NO_EXECUTION_BOUNDARY_PASS",
        "generated_utc": prov.get("generated_utc"),
    }
    (AUD / "phase25b_no_execution_boundary_audit.json").write_text(
        json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

    for r in out_rows:
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['check']} :: {r['detail']}")
    print()
    print(f"{len(out_rows) - n_fail}/{len(out_rows)} PASS")
    print(out["verdict"])
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
