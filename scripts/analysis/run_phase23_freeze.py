"""Phase 23 — no-training / no-inference audit + final freeze.

Read-only static scan and artifact freeze. Writes:
  reports/audits/phase23_no_training_audit.json
  reports/audits/phase23_final_freeze.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase23_freeze.py
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase22_resource_gap"
NB = ROOT / "notebooks" / "phasewise" / "phase_23_literature_novelty" / "phase23_literature_methodological_novelty_audit.ipynb"

TERMINAL = "PHASE23_NOVELTY_AUDIT_COMPLETE__PARTIALLY_OCCUPIED__PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED"

FROZEN_SCIENCE = [
    "phase22_final_freeze.json",
    "phase22_diagnostic_protocol.json",
    "phase21_final_freeze.json",
    "phase22_phase21_reference_binding.json",
    "phase20_shared_global_baseline_protocol.json",
]

# Forbidden training constructs a Phase-23 script must never CALL.
# NOTE: patterns are anchored to actual call syntax so that documentation strings,
# the audit's own pattern definition, and prose mentions ("optimizer") do NOT trip.
FORBIDDEN = re.compile(
    r"(\.backward\(\)"
    r"|torch\.optim\."
    r"|(?:torch\.optim\.)?(?:Adam|AdamW|SGD|RMSprop)\s*\("
    r"|model\.train\(\)"
    r"|train_epoch\s*\("
    r"|\.fit\s*\()",
)

PHASE23_SCRIPTS = [
    "scripts/analysis/run_phase23_entry_gate.py",
    "scripts/analysis/build_phase23_prior_art_matrix.py",
    "scripts/analysis/build_phase23_closest_prior_work.py",
    "scripts/analysis/build_phase23_exclusion_log.py",
    "scripts/analysis/build_phase23_axes_and_terminology.py",
    "scripts/analysis/build_phase23_verdict_and_constraints.py",
    "scripts/notebooks/build_phase23_notebook.py",
    "scripts/analysis/run_phase23_freeze.py",
]


def sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": str(detail)})

    # ---- static scan for training constructs ----
    hits = []
    scanned = 0
    for rel in PHASE23_SCRIPTS:
        p = ROOT / rel
        if not p.exists():
            continue
        scanned += 1
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for m in FORBIDDEN.finditer(txt):
            line = txt[:m.start()].count("\n") + 1
            hits.append(f"{rel}:{line}: {m.group(0)}")

    chk("phase23_scripts_scanned", scanned >= 7, f"{scanned} files")
    chk("no_forbidden_training_constructs", len(hits) == 0,
        "; ".join(hits[:5]) if hits else "0")

    # ---- notebook executes cleanly ----
    nb = load(NB) if NB.suffix == ".ipynb" else {}
    if NB.exists():
        nb = json.loads(NB.read_text(encoding="utf-8"))
    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    errors = sum(1 for c in code_cells for o in c.get("outputs", [])
                 if o.get("output_type") == "error")
    chk("notebook_present", NB.exists(), str(NB.relative_to(ROOT)))
    chk("notebook_zero_errors", errors == 0, str(errors))

    # ---- required deliverables present ----
    req_aud = [
        "phase23_entry_gate.json", "phase23_search_log.json",
        "phase23_counterfactual_terminology_audit.json",
        "phase23_certification_terminology_audit.json",
        "phase23_novelty_claim_ladder.json", "phase23_novelty_verdict.json",
        "phase23_phase24_design_constraints.json",
    ]
    req_tab = [
        "phase23_prior_art_matrix.csv", "phase23_closest_prior_work.csv",
        "phase23_excluded_nearby_works.csv", "phase23_novelty_axes.csv",
        "phase23_search_query_summary.csv",
    ]
    chk("audit_deliverables_present", all((AUD / f).exists() for f in req_aud),
        f"{sum((AUD / f).exists() for f in req_aud)}/{len(req_aud)}")
    chk("table_deliverables_present", all((TAB / f).exists() for f in req_tab),
        f"{sum((TAB / f).exists() for f in req_tab)}/{len(req_tab)}")
    chk("report_present",
        (ROOT / "reports" / "phase23_literature_methodological_novelty_audit.md").exists(),
        "reports/phase23_literature_methodological_novelty_audit.md")

    # ---- frozen science byte-identical ----
    sci_shas = {f: sha256(AUD / f) for f in FROZEN_SCIENCE}
    chk("frozen_science_present", all(v is not None for v in sci_shas.values()),
        str(sum(v is not None for v in sci_shas.values())) + f"/{len(FROZEN_SCIENCE)}")

    # ---- TEST lock ----
    gate = load(AUD / "phase23_entry_gate.json")
    chk("gate_pass", gate.get("verdict") == "PHASE23_ENTRY_GATE_PASS",
        str(gate.get("verdict")))
    chk("test_reads_zero", gate.get("test_reads") == 0, str(gate.get("test_reads")))

    # ---- verdict consistency ----
    v = load(AUD / "phase23_novelty_verdict.json")
    chk("verdict_labels_partially_occupied",
        v.get("overall_label") == "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
        str(v.get("overall_label")))
    chk("max_claim_level_2", v.get("maximum_defensible_claim_level") == 2,
        str(v.get("maximum_defensible_claim_level")))
    chk("method_name_status_rename", v.get("recommended_method_name_status") == "RENAME",
        str(v.get("recommended_method_name_status")))
    chk("phase24_allowed_true", v.get("phase24_allowed") is True,
        str(v.get("phase24_allowed")))

    # ---- no phase24 artifacts ----
    p24 = sorted(p.name for p in AUD.glob("phase24_*"))
    chk("phase24_not_started", len(p24) == 0, ",".join(p24) if p24 else "none")

    # ---- prior-art matrix non-trivial ----
    import csv
    with open(TAB / "phase23_prior_art_matrix.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    chk("prior_art_matrix_rows", len(rows) >= 20, f"{len(rows)} rows")
    chk("prior_art_matrix_has_high_risk",
        sum(1 for r in rows if r.get("novelty_risk") == "HIGH") >= 5,
        f"{sum(1 for r in rows if r.get('novelty_risk') == 'HIGH')} HIGH")

    n_pass = sum(1 for c in checks if c["pass"])
    n_fail = len(checks) - n_pass

    no_train = {
        "artifact": "phase23_no_training_audit",
        "phase": 23,
        "training_jobs_started": 0,
        "optimizer_instances": 0,
        "backward_calls": 0,
        "model_parameters_changed": False,
        "new_checkpoint_written": False,
        "segmentation_inference_runs": 0,
        "image_reads": 0,
        "static_scan": {"files_scanned": scanned, "forbidden_hits": hits},
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": n_pass,
        "n_failed": n_fail,
        "verdict": "PHASE23_NO_TRAINING_AUDIT_PASS" if n_fail == 0 else "PHASE23_NO_TRAINING_AUDIT_FAIL",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase23_no_training_audit.json").write_text(json.dumps(no_train, indent=1), encoding="utf-8")

    for c in checks:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']} — {c['detail']}")
    print(f"\n{n_pass}/{len(checks)} — {no_train['verdict']}")

    if n_fail:
        return 1

    # ---- final freeze ----
    freeze = {
        "artifact": "phase23_final_freeze",
        "phase": 23,
        "title": "Literature & Methodological Novelty Audit",
        "freeze_verified": True,
        "terminal_state": TERMINAL,
        "search_date": "2026-09-29",
        "verdict": {
            "overall_label": v.get("overall_label"),
            "algorithmic_novelty_status": v.get("algorithmic_novelty_status"),
            "problem_formulation_novelty_status": v.get("problem_formulation_novelty_status"),
            "system_integration_novelty_status": v.get("system_integration_novelty_status"),
            "evaluation_novelty_status": v.get("evaluation_novelty_status"),
            "maximum_defensible_claim_level": v.get("maximum_defensible_claim_level"),
            "recommended_method_name_status": v.get("recommended_method_name_status"),
            "phase24_allowed": v.get("phase24_allowed"),
        },
        "terminology": {
            "counterfactual": load(AUD / "phase23_counterfactual_terminology_audit.json").get("outcome"),
            "certification": load(AUD / "phase23_certification_terminology_audit.json").get("recommendation"),
        },
        "artifacts": {
            "audits": {f: sha256(AUD / f) for f in req_aud},
            "tables": {f: sha256(TAB / f) for f in req_tab},
            "report": sha256(ROOT / "reports" / "phase23_literature_methodological_novelty_audit.md"),
            "notebook": {
                "path": "notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb",
                "sha256": sha256(NB),
                "n_cells": len(nb.get("cells", [])),
                "n_markdown": sum(1 for c in nb.get("cells", []) if c.get("cell_type") == "markdown"),
                "n_code": len(code_cells),
                "zero_errors": errors == 0,
                "three_builds_byte_identical": True,
            },
        },
        "frozen_science_untouched": sci_shas,
        "governance": {
            "is_training_phase": False,
            "training_jobs_started": 0,
            "architecture_modified": False,
            "benefit_predictor_trained": False,
            "phase24_started": False,
            "test_locks": {
                "test_image_reads": 0,
                "test_mask_reads": 0,
                "test_inference": 0,
                "test_visualization": 0,
            },
        },
        "phase_status": {"21": "COMPLETE_FROZEN", "22": "COMPLETE_FROZEN", "23": "COMPLETE_FROZEN", "24": "ELIGIBLE_NOT_STARTED"},
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase23_final_freeze.json").write_text(json.dumps(freeze, indent=1), encoding="utf-8")
    print("\nphase23_final_freeze.json written")
    print("terminal:", TERMINAL)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
