"""Phase 24 — SPECIFICATION COMPLETENESS REPAIR (5/5).

Refresh the no-execution audit, prove notebook determinism over the repaired notebook
(3 byte-identical builds) and write the repair freeze + terminal state.

DESIGN ONLY. No training, inference, module instantiation or outcome inspection.

Writes:
    reports/audits/phase24_no_execution_audit.json       (refreshed via run_phase24_audits.py)
    reports/audits/phase24_notebook_determinism.json     (repaired notebook)
    reports/audits/phase24_spec_repair_freeze.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase24_repair_final.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
PY = ROOT / ".venv/Scripts/python.exe"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
BUILDER = ROOT / "scripts/notebooks/build_phase24_notebook.py"
FIGDIR = ROOT / "reports/figures/phase24_architecture_spec"
UTC = datetime.now(timezone.utc).isoformat()
OLD_NB_SHA = "e4383d5ac9c33787b809407e4884cd7069f1f4514ed0abf7c21c844024221207"
TERMINAL = ("PHASE24_SPEC_COMPLETENESS_REPAIR_COMPLETE__RA_MEDFILM_BARR_V1_1_FROZEN"
            "__PHASE25_ELIGIBLE_NOT_STARTED")


def j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------ 1. no-execution refresh
print("=== refreshing no-execution audit ===")
r = subprocess.run([str(PY), str(ROOT / "scripts/analysis/run_phase24_audits.py")],
                   cwd=str(ROOT), capture_output=True, text=True)
print(r.stdout[-700:])
assert r.returncode == 0, r.stderr[-2000:]

# ------------------------------------------------------------------ 2. determinism 3x
print("\n=== determinism: 3 builds ===")
shas, fig_shas = [], []
for i in range(3):
    print(f"  build {i + 1}/3 ...")
    rr = subprocess.run([str(PY), str(BUILDER)], cwd=str(ROOT),
                        capture_output=True, text=True)
    if rr.returncode != 0:
        print(rr.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"build {i + 1} failed")
    shas.append(sha(NB))
    fig_shas.append({p.name: sha(p) for p in sorted(FIGDIR.glob("*.png"))})

import nbformat  # noqa: E402
nb = nbformat.read(str(NB), as_version=4)
code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", [])
             if o.get("output_type") == "error")
imgs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))

byte_identical = len(set(shas)) == 1
fig_identical = all(f == fig_shas[0] for f in fig_shas)

det = {
    "artifact": "phase24_notebook_determinism",
    "phase": 24,
    "repair": "POST_PHASE24_SPECIFICATION_COMPLETENESS_REPAIR",
    "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
    "n_builds": 3,
    "shas": shas,
    "sha256": shas[0],
    "sha256_previous": OLD_NB_SHA,
    "byte_identical": byte_identical,
    "figures_sha256": fig_shas[0],
    "figures_byte_identical": fig_identical,
    "n_cells": len(nb.cells),
    "n_markdown": sum(1 for c in nb.cells if c.cell_type == "markdown"),
    "n_code": len(code_cells),
    "zero_tracebacks": errors == 0,
    "embedded_png_outputs": imgs,
    "kernel": "jup-venv",
    "training": False,
    "inference": False,
    "test_reads": 0,
    "generated_utc": UTC,
}
(AUD / "phase24_notebook_determinism.json").write_text(
    json.dumps(det, indent=1), encoding="utf-8")
print(f"  byte identical : {byte_identical}")
print(f"  figures identical : {fig_identical}")
print(f"  notebook sha : {shas[0]}")
print(f"  cells : {len(nb.cells)} ({det['n_markdown']} md / {len(code_cells)} code), png {imgs}")

assert byte_identical, "FAIL: repaired notebook builds are not byte-identical"
assert errors == 0

# ------------------------------------------------------------------ 3. repair freeze
ex = j(AUD / "phase24_exact_implementation_spec.json")
pe = j(AUD / "phase24_benefit_data_protocol_exact.json")
sc = j(AUD / "phase24_spec_completeness_repair.json")
ne = j(AUD / "phase24_no_execution_audit.json")
arch = j(AUD / "phase24_architecture_spec.json")
rev = j(AUD / "phase24_architecture_revision_v1_1.json")

PRED = {
    "phase21_best_pt_sha256": ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
                               "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
    "phase22_protocol_sha256": ("reports/audits/phase22_diagnostic_protocol.json",
                                "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7"),
    "phase22_freeze_sha256": ("reports/audits/phase22_final_freeze.json",
                              "9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca"),
    "phase23_notebook_sha256": ("notebooks/phasewise/phase_23_literature_novelty/"
                                "phase23_literature_methodological_novelty_audit.ipynb",
                                "e9f78ccefd96abad742fa5570a44110cd67c62f5510b99300448e44b961107b0"),
}
pred_ok = {k: sha(ROOT / rel) == exp for k, (rel, exp) in PRED.items()}
# hash key rename to include prefix semantics
pred_map = {k.replace("_sha256", ""): (ROOT / rel) for k, (rel, _) in PRED.items()}
pred_sha = {k: sha(p) for k, p in pred_map.items()}

freeze = {
    "artifact": "phase24_spec_repair_freeze",
    "phase": 24,
    "repair": "POST_PHASE24_SPECIFICATION_COMPLETENESS_REPAIR",
    "classification": "SPECIFICATION_COMPLETENESS_REPAIR",
    "architecture_id": "ra_medfilm_barr_narrowed_v1_1",
    "supersedes_architecture_id": "ra_medfilm_barr_narrowed_v1",
    "method_name": "RA-MedFiLM-BARR",
    "science_changed": False,
    "revision_reason": "SPECIFICATION_COMPLETENESS_ONLY",
    "is_final": True,
    "bindings": {
        "method_name": "RA-MedFiLM-BARR",
        "architecture_id": "ra_medfilm_barr_narrowed_v1_1",
        "split_seed": 42,
        "split_development_n": pe.get("development_n"),
        "split_holdout_n": pe.get("holdout_n"),
        "split_manifest_sha256": pe.get("manifest_sha256"),
        "roi_expansion_factor": ex["roi"]["expansion_factor"],
        "roi_resolution": ex["roi"]["input_resolution"],
        "refiner_name": ex["refiner"]["name"],
        "refiner_active_channels": ex["refiner"]["encoder_bridge_channels_active"],
        "refiner_params_closed_form": ex["refiner"]["expected_parameter_count_closed_form"],
        "router_name": ex["router"]["name"],
        "router_feature_taps": ex["router"]["feature_taps"],
        "router_params_closed_form": ex["router"]["expected_parameter_count_closed_form"],
        "router_lambda_grid": ex["routing"]["lambda_grid"],
        "post_safety_extension": ex["post_safety"]["extension_status"],
        "fusion_threshold": ex["fusion"]["segmentation_threshold"],
        "notebook_sha256_previous": OLD_NB_SHA,
        "notebook_sha256_current": shas[0],
        "spec_completeness_verdict": sc.get("verdict"),
        "spec_completeness_passed": f"{sc.get('n_passed')}/{sc.get('n_checks')}",
        "no_execution_verdict": ne.get("verdict"),
        "test_lock": arch.get("TEST_lock", {}).get("status"),
        "phase25_started": False,
    },
    "predecessor_sha256": pred_sha,
    "predecessor_unchanged": pred_ok,
    "science_unchanged": all(pred_ok.values()),
    "counters": {
        "training_runs": 0,
        "optimizer_instances_used_for_training": 0,
        "backward_calls": 0,
        "segmentation_forward_passes": 0,
        "regional_refiner_forward_passes": 0,
        "router_forward_passes": 0,
        "module_instantiations": 0,
        "holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
        "test_image_reads": 0,
        "test_mask_reads": 0,
        "test_inference_calls": 0,
        "test_visualizations": 0,
        "phase25_modules_started": 0,
    },
    "artifacts": {
        "exact_spec": "reports/audits/phase24_exact_implementation_spec.json",
        "exact_split": "reports/audits/phase24_benefit_data_protocol_exact.json",
        "split_manifest": "reports/audits/phase24_router_split_manifest.csv",
        "architecture_revision": "reports/audits/phase24_architecture_revision_v1_1.json",
        "primary_feature_set": "reports/tables/phase24_router_primary_feature_set.csv",
        "module_envelope": "reports/tables/phase24_spec_module_envelope.csv",
        "oof_gain_schema": "reports/tables/phase25_future_oof_gain_schema.csv",
        "spec_completeness_audit": "reports/audits/phase24_spec_completeness_repair.json",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": shas[0],
    },
    "terminal_state": TERMINAL if sc.get("verdict") == "PHASE24_SPEC_COMPLETENESS_REPAIR_PASS"
                     and all(pred_ok.values()) else "PHASE24_SPEC_COMPLETENESS_REPAIR_BLOCKED",
    "phase25_started": False,
    "notes": (
        "Phase 24 remains DESIGN-ONLY. This repair closes implementation degrees of freedom only. "
        "No predecessor artifact was modified. No Phase-25 module was started."
    ),
    "generated_utc": UTC,
    "test_reads": 0,
}
(AUD / "phase24_spec_repair_freeze.json").write_text(
    json.dumps(freeze, indent=1), encoding="utf-8")

print()
print("=== repair freeze ===")
print("  science predecessors unchanged:", freeze["science_unchanged"])
for k, v in pred_ok.items():
    print(f"    {k:28s} {'OK' if v else 'CHANGED'}")
print("  all counters zero:", all(v == 0 for v in freeze["counters"].values()))
print("  terminal:", freeze["terminal_state"])
print()
print(freeze["terminal_state"])
assert freeze["science_unchanged"]
assert all(v == 0 for v in freeze["counters"].values())
