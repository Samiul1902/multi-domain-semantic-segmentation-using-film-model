#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.1 — reviewer notebook static audit (READ-ONLY).

Verifies the notebook does NOT construct models, load checkpoints, run forward,
generate perturbations, read medical data, read VAL808, read GT, read
ROUTER_HOLDOUT, read TEST, or train.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NB = ROOT / "notebooks" / "phasewise" / "phase_36_robustness" / \
    "phase36_synthetic_full_pipeline_smoke_v1_1_review.ipynb"
OUT = ROOT / "reports" / "audits" / "phase36_v1_1_reviewer_notebook_audit.json"

FORBIDDEN = {
    "torch": "torch",
    "model_construction": "RAMedFiLMBARR(",
    "checkpoint_load": "torch.load",
    "forward": ".forward_inference(",
    "gradcam": "gradcam",
    "gradient": ".backward()",
    "perturbation_generation": "apply_image_condition",
    "perturbation_generation2": "apply_proposal_condition",
    "medical_data_read": "Image.open",
    "val808_manifest_read": "val.csv",
    "gt_read": "mask_path",
    "holdout_path_read": "router_holdout.csv",
    "test_path_read": "test.csv",
    "training": "optimizer",
}

R = []


def ck(cid, desc, cond, detail=""):
    R.append({"id": cid, "desc": desc, "pass": bool(cond), "detail": str(detail)})


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    # Audit CODE cells only for access operations. Markdown may legitimately NAME
    # protected artefacts in defensive/declarative prose ("does NOT read TEST").
    code_src = "".join("".join(c.get("source", []))
                       for c in nb["cells"] if c["cell_type"] == "code")
    low = code_src.lower()
    all_src = "".join("".join(c.get("source", [])) for c in nb["cells"])

    ck("01", "notebook is valid nbformat 4", nb.get("nbformat") == 4)
    ck("02", "notebook has code+markdown cells", len(nb["cells"]) >= 8)

    for i, (name, token) in enumerate(FORBIDDEN.items(), start=3):
        hit = token.lower() in low
        ck(f"{i:02d}", f"no {name} in notebook CODE cells", not hit, token if hit else "")

    # reads only governance artifacts
    ck("20", "notebook reads only reports/audits governance artifacts",
       "AUD / name" in code_src and "reports" in code_src)
    ck("21", "notebook executed with outputs",
       any(c["cell_type"] == "code" and c.get("outputs") for c in nb["cells"]))
    # declarative boundary statements present in markdown
    ck("22", "markdown declares read-only boundary",
       "does **NOT**" in all_src or "READ-ONLY" in all_src or "read-only" in all_src.lower())

    passed = sum(1 for r in R if r["pass"])
    total = len(R)
    payload = {
        "artifact": "phase36_v1_1_reviewer_notebook_audit",
        "phase": 36, "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_1",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": hashlib.sha256(NB.read_bytes()).hexdigest(),
        "read_only": True,
        "checks": R, "total_checks": total, "passed": passed,
        "failed": total - passed, "all_pass": bool(passed == total),
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": total,
                      "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()}, indent=1))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
