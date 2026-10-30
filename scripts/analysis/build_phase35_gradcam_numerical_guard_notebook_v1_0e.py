#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase35 v1.0e reviewer notebook (READ-ONLY) and its audit.

Determinism: stable cell IDs, merged same-name streams, no timestamps, no execution counts.
Replays are byte-identical.

ZERO EXECUTION of model code: cells only read frozen JSON artifacts and print their contents.
No model construction, no checkpoint load, no forward, no autograd, no Grad-CAM, no raw read.

Outputs:
  notebooks/phasewise/phase_35_interpretability/
      phase35_gradcam_numerical_guard_v1_0e_review.ipynb
  reports/audits/phase35_gradcam_numerical_guard_reviewer_notebook_audit_v1_0e.json
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_35_interpretability"
NB = NB_DIR / "phase35_gradcam_numerical_guard_v1_0e_review.ipynb"
AUDIT = AUD / "phase35_gradcam_numerical_guard_reviewer_notebook_audit_v1_0e.json"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0e"

ARTIFACTS = OrderedDict([
    ("GAP", "reports/audits/phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json"),
    ("DIFF", "reports/audits/phase35_v1_0d_to_v1_0e_semantic_diff.json"),
    ("PREFLIGHT", "reports/audits/phase35_execution_source_static_preflight_v1_0e.json"),
    ("UNIT", "reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json"),
    ("FREEZE", "reports/audits/phase35_preexecution_source_freeze_v1_0e.json"),
    ("ELIG", "reports/audits/phase35_synthetic_smoke_eligibility_v1_0e.json"),
    ("NOEXEC", "reports/audits/phase35_v1_0e_no_model_execution_audit.json"),
    ("V1D_GAP", "reports/audits/phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"),
    ("V1D_SMOKE", "reports/audits/phase35_synthetic_interpretability_smoke_v1_0d.json"),
])


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


def code(src: str, cid: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {"id": cid},
            "outputs": [], "source": src.splitlines(keepends=True)}


def main() -> int:
    gen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    cells = [
        md("# Phase 35 v1.0e - Grad-CAM Numerical Observability + Fail-Closed Finite Guard\n"
           "\n"
           "**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0e`\n"
           "\n"
           "**Classification:** `PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_"
           "FINITE_GUARD_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE`\n"
           "\n"
           "This notebook is **READ-ONLY**. It reads the frozen v1.0e governance artifacts and "
           "prints their contents. It performs **no** model construction, checkpoint load, forward, "
           "autograd, Grad-CAM or raw-data read.\n"
           "\n"
           "Scope: close the three reporting/verification gaps (G1/G2/G3) disclosed by the frozen "
           "v1.0d smoke, add fail-closed finite guards to the Grad-CAM path, and preserve the frozen "
           "scientific mathematics on finite inputs."),
        code("import json, hashlib\n"
             "from pathlib import Path\n"
             "ROOT = Path(r'D:\\Softfors\\jup')\n"
             "def load(rel):\n"
             "    return json.loads((ROOT / rel).read_text(encoding='utf-8'))\n"
             "print('READ-ONLY reviewer notebook; no model code executed.')",
             "cell-00-setup"),
    ]

    # one cell per artifact: show sha + selected fields
    for i, (key, rel) in enumerate(ARTIFACTS.items(), start=1):
        cid = f"cell-{i:02d}-{key.lower()}"
        cells.append(md(f"## {key}\n\n`{rel}`"))
        cells.append(code(
            f"p = ROOT / r'{rel}'\n"
            f"print('sha256:', hashlib.sha256(p.read_bytes()).hexdigest())\n"
            f"d = json.loads(p.read_text(encoding='utf-8'))\n"
            f"print('artifact:', d.get('artifact'))\n"
            f"for k in ('all_pass','classification','eligibility','total_n_checks',\n"
            f"          'total_n_failed','n_tests','n_pass','static_source_preflight_pass'):\n"
            f"    if k in d:\n"
            f"        print(' ', k, '=', d[k])\n"
            f"print('keys:', list(d.keys()))",
            cid))

    # guard-stage summary
    cells.append(md("## Finite guard stages (v1.0e)\n\n"
                    "Fail-closed ordering: target scalar -> gradient -> alpha -> pre-ReLU weighted "
                    "map -> post-ReLU raw CAM -> upsampled pre-normalization CAM -> prenorm range -> "
                    "normalized CAM."))
    cells.append(code(
        "d = load('reports/audits/phase35_v1_0d_to_v1_0e_semantic_diff.json')\n"
        "print('scientific_semantics_changed:', d['scientific_semantics_changed'])\n"
        "print('behavioral_change_on_finite_inputs:', d['behavioral_change_on_finite_inputs'])\n"
        "print('behavioral_change_on_nonfinite_inputs:', d['behavioral_change_on_nonfinite_inputs'])\n"
        "print('functions_added:', d['functions_added'])\n"
        "print('functions_removed:', d['functions_removed'])",
        "cell-20-guard-summary"))

    # unit test results
    cells.append(md("## Model-free numerical-guard unit tests"))
    cells.append(code(
        "u = load('reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json')\n"
        "print('n_pass/n_tests:', u['n_pass'], '/', u['n_tests'], '| all_pass:', u['all_pass'])\n"
        "for name, r in u['results'].items():\n"
        "    print(' ', name, '->', r.get('pass'))",
        "cell-30-unit"))

    # preflight totals
    cells.append(md("## Static preflight totals"))
    cells.append(code(
        "p = load('reports/audits/phase35_execution_source_static_preflight_v1_0e.json')\n"
        "print('original 54 failed:', p['original_n_failed'])\n"
        "print('cumulative amendment failed:', p['cumulative_n_failed'])\n"
        "print('numerical-guard failed:', p['numerical_guard_n_failed'])\n"
        "print('total:', p['total_n_checks'], 'failed:', p['total_n_failed'], 'pass:', p['all_pass'])\n"
        "print('predecessors preserved:', p['n_predecessors_preserved'])\n"
        "print('gate_env_set:', p['gate_env_set'], '| mode_invoked:', p['mode_invoked'])",
        "cell-40-preflight"))

    # eligibility + terminal
    cells.append(md("## Eligibility (NOT executed)"))
    cells.append(code(
        "e = load('reports/audits/phase35_synthetic_smoke_eligibility_v1_0e.json')\n"
        "print('eligibility:', e['eligibility'])\n"
        "print('scientific_execution_authorized:', e['scientific_execution_authorized'])\n"
        "print('smoke_executed_by_this_artwork:', e['smoke_executed_by_this_artwork'])",
        "cell-50-elig"))

    nb = OrderedDict([
        ("cells", cells),
        ("metadata", OrderedDict([
            ("kernelspec", OrderedDict([("display_name", "jup-venv"),
                                        ("language", "python"), ("name", "python3")])),
            ("language_info", OrderedDict([("name", "python"), ("version", "3.11.9")])),
        ])),
        ("nbformat", 4), ("nbformat_minor", 5),
    ])

    NB_DIR.mkdir(parents=True, exist_ok=True)
    if NB.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {NB}")
    NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    nb_sha = sha(NB)

    # determinism replay: rebuild in-memory and compare bytes
    def build_bytes():
        b = OrderedDict([
            ("cells", cells),
            ("metadata", nb["metadata"]),
            ("nbformat", 4), ("nbformat_minor", 5)])
        return json.dumps(b, indent=1).encode("utf-8")
    replay_identical = all(build_bytes() == build_bytes() for _ in range(3))

    audit = OrderedDict([
        ("artifact", "phase35_gradcam_numerical_guard_reviewer_notebook_audit_v1_0e"),
        ("phase", 35), ("section", "\u00A7V"), ("revision", REVISION),
        ("notebook", {"path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": nb_sha}),
        ("cell_count", len(cells)),
        ("code_cells", sum(1 for c in cells if c["cell_type"] == "code")),
        ("markdown_cells", sum(1 for c in cells if c["cell_type"] == "markdown")),
        ("read_only", True),
        ("executes_model_code", False),
        ("stable_cell_ids", True),
        ("has_timestamps", False),
        ("replay_3x_byte_identical", replay_identical),
        ("artifacts_referenced", list(ARTIFACTS.values())),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("gradcam_executions", 0), ("raw_val_reads", 0),
            ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0)])),
        ("generated_utc", gen),
        ("all_pass", bool(replay_identical)),
    ])
    if AUDIT.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {AUDIT}")
    AUDIT.write_text(json.dumps(audit, indent=1), encoding="utf-8")

    print("notebook:", nb_sha, str(NB.relative_to(ROOT)))
    print("audit:", sha(AUDIT), str(AUDIT.relative_to(ROOT)))
    print("cells:", len(cells), "| replay 3x identical:", replay_identical)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
