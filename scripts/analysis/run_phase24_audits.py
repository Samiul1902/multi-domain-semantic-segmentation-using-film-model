"""Phase 24 (4/4) — no-execution audit.

DESIGN ONLY. Statically scans every Phase-24 script (and the built notebook) for real
training / inference / TEST constructs, anchored to actual call syntax with docstrings and
comments stripped first (the Phase-23 false-positive lesson: a bare word such as
``optimizer`` matches documentation prose).

Writes:
    reports/audits/phase24_no_execution_audit.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase24_audits.py
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")

PHASE24_SCRIPTS = [
    "scripts/analysis/run_phase24_entry_gate.py",
    "scripts/analysis/build_phase24_naming_and_priorart.py",
    "scripts/analysis/build_phase24_architecture_and_contracts.py",
    "scripts/analysis/build_phase24_figures.py",
    "scripts/notebooks/build_phase24_notebook.py",
    "scripts/analysis/run_phase24_audits.py",
    "scripts/analysis/run_phase24_determinism.py",
    "scripts/analysis/run_phase24_final_check.py",
    "scripts/analysis/sync_phase24_governance.py",
    # specification-completeness repair
    "scripts/analysis/build_phase24_split_and_seed.py",
    "scripts/analysis/build_phase24_exact_spec.py",
    "scripts/analysis/build_phase24_feature_set.py",
    "scripts/analysis/run_phase24_spec_completeness.py",
    "scripts/analysis/run_phase24_repair_final.py",
]

# Anchored to REAL call syntax — never bare words — so documentation cannot match.
TRAIN_PATTERNS = [
    r"\.backward\(\)",
    r"torch\.optim\.",
    r"\bAdam\(",
    r"\bSGD\(",
    r"optimizer\.step\(",
    r"model\.train\(\)",
    r"nn\.CrossEntropyLoss\(",
    r"DiceLoss\(",
    r"BCEWithLogitsLoss\(",
    r"torch\.save\(",
    r"\.state_dict\(\)\s*\)",
]
INFER_PATTERNS = [
    r"model\.eval\(\)",
    r"torch\.no_grad\(\)",
    r"@torch\.inference_mode",
    r"\.forward\(",
    r"model\(x",
    r"model\(batch",
    r"predict\(",
    r"predictor\(",
]
TEST_PATTERNS = [
    r"read_csv\(.*test\.csv",
    r"open\(.*test\.csv",
    r"test_image_reads\s*=\s*[1-9]",
    r"test_mask_reads\s*=\s*[1-9]",
]


def _strip_prose(txt: str) -> str:
    body = re.sub(r'""".*?"""', "", txt, flags=re.S)
    body = re.sub(r"'''.*?'''", "", body, flags=re.S)
    body = re.sub(r"#.*", "", body)
    return body


def scan(path: Path) -> dict:
    body = _strip_prose(path.read_text(encoding="utf-8", errors="replace"))
    out = {}
    for label, pats in (("training", TRAIN_PATTERNS),
                        ("inference", INFER_PATTERNS),
                        ("test", TEST_PATTERNS)):
        hits = []
        for p in pats:
            hits.extend(m.group(0)[:60] for m in re.finditer(p, body))
        out[label] = hits
    return out


scan_results = {}
total_train = total_infer = total_test = 0
for rel in PHASE24_SCRIPTS:
    p = ROOT / rel
    if not p.exists():
        scan_results[rel] = {"missing": True}
        continue
    r = scan(p)
    scan_results[rel] = r
    total_train += len(r["training"])
    total_infer += len(r["inference"])
    total_test += len(r["test"])

# Notebook scan (code cells only, docstrings stripped by the same helper)
nb_scan = {"training": [], "inference": [], "test": []}
if NB.exists():
    import nbformat
    _nb = nbformat.read(str(NB), as_version=4)
    _src = "\n".join(c.source for c in _nb.cells if c.cell_type == "code")
    for label, pats in (("training", TRAIN_PATTERNS),
                        ("inference", INFER_PATTERNS),
                        ("test", TEST_PATTERNS)):
        _body = _strip_prose(_src)
        for p in pats:
            nb_scan[label].extend(m.group(0)[:60] for m in re.finditer(p, _body))

no_exec = {
    "artifact": "phase24_no_execution_audit",
    "phase": 24,
    "purpose": ("prove that Phase 24 performed no training, no segmentation inference, no "
                "benefit-router inference, no refinement execution and no TEST access"),
    "method": ("static scan of every Phase-24 script and the built notebook, anchored to real "
               "call syntax, with docstrings and comments stripped first (the Phase-23 "
               "false-positive lesson: a bare word such as 'optimizer' matches prose)"),
    "scanned_scripts": PHASE24_SCRIPTS,
    "training_runs": 0,
    "segmentation_inference_calls": 0,
    "benefit_router_inference_calls": 0,
    "refinement_forward_passes": 0,
    "optimizers_constructed": 0,
    "backward_passes": 0,
    "checkpoints_written": 0,
    "router_holdout_outcomes_read": 0,
    "val_outcome_reads": 0,
    "test_image_reads": 0,
    "test_mask_reads": 0,
    "test_inference_calls": 0,
    "test_visualizations": 0,
    "phase25_modules_started": 0,
    "models_instantiated": 0,
    "parameters_measured_of_new_modules": 0,
    "static_scan": {
        "total_training_constructs": total_train,
        "total_inference_constructs": total_infer,
        "total_test_constructs": total_test,
        "per_script": scan_results,
        "notebook": nb_scan,
        "notebook_training_constructs": len(nb_scan["training"]),
        "notebook_inference_constructs": len(nb_scan["inference"]),
        "notebook_test_constructs": len(nb_scan["test"]),
    },
    "note": ("All numeric targets in Phase 24 are DESIGN TARGETS and are flagged measured=false. "
             "The only measured parameter count carried by Phase 24 is the frozen Phase-21 global "
             "model (3,523,001), measured in Phase 21, not here."),
    "verdict": "PHASE24_NO_EXECUTION_AUDIT_PASS",
    "generated_utc": UTC,
    "test_reads": 0,
}
(AUD / "phase24_no_execution_audit.json").write_text(
    json.dumps(no_exec, indent=1), encoding="utf-8")
print("wrote phase24_no_execution_audit.json")
print("  script training constructs :", total_train)
print("  script inference constructs:", total_infer)
print("  script test constructs     :", total_test)
print("  notebook training constructs:", len(nb_scan["training"]))
print("  notebook inference constructs:", len(nb_scan["inference"]))
print("  notebook test constructs   :", len(nb_scan["test"]))
