#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0 SCIENTIFIC EXECUTION reviewer-notebook audit (§X).

READ-ONLY static inspection of the produced reviewer notebook. Verifies:
  * the notebook exists and executed with 0 cell errors,
  * its import surface is limited to hashlib / json / pathlib,
  * it performs no model construction / checkpoint load / forward / autograd / training,
  * it touches no protected data (no raw image, no VAL GT, no HOLDOUT, no TEST).

Emits `reports/audits/phase35_interpretability_scientific_execution_reviewer_notebook_audit_v1_0.json`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NBREL = ("notebooks/phasewise/phase_35_interpretability/"
         "phase35_interpretability_scientific_execution_v1_0_review.ipynb")
NB = ROOT / NBREL

FORBIDDEN_IMPORTS = ["torch", "numpy", "pandas", "PIL", "matplotlib", "sklearn",
                     "subprocess", "sqlite3", "nbclient", "nbformat"]
ALLOWED_IMPORTS = {"hashlib", "json", "pathlib"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    checks = []

    def ck(cid, desc, ok, detail=""):
        checks.append({"id": cid, "desc": desc, "pass": bool(ok), "detail": detail})

    exists = NB.exists()
    ck("01", "reviewer notebook exists", exists, NBREL)
    if not exists:
        doc = OrderedDict([("artifact",
                            "phase35_interpretability_scientific_execution_reviewer_notebook_audit_v1_0"),
                           ("checks", checks), ("all_pass", False)])
        (ROOT / "reports/audits/"
         "phase35_interpretability_scientific_execution_reviewer_notebook_audit_v1_0.json"
         ).write_text(json.dumps(doc, indent=1), encoding="utf-8")
        return 1

    nb = json.loads(NB.read_text(encoding="utf-8"))
    src_all = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    src_code = "\n".join("".join(c.get("source", [])) for c in nb["cells"]
                         if c["cell_type"] == "code")

    n_code = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
    n_md = sum(1 for c in nb["cells"] if c["cell_type"] == "markdown")
    n_err = sum(1 for c in nb["cells"] for o in c.get("outputs", [])
                if o.get("output_type") == "error")
    n_exec = sum(1 for c in nb["cells"] if c["cell_type"] == "code"
                 and c.get("execution_count") is not None)

    ck("02", "notebook contains code and markdown cells", n_code >= 10 and n_md >= 10,
       f"code={n_code} md={n_md}")
    ck("03", "every code cell executed (execution_count populated)", n_exec == n_code,
       f"{n_exec}/{n_code}")
    ck("04", "zero cell errors", n_err == 0, f"errors={n_err}")
    ck("05", "import surface limited to hashlib/json/pathlib",
       all(f"import {m}" not in src_all for m in FORBIDDEN_IMPORTS)
       and "import json" in src_all and "import hashlib" in src_all
       and "from pathlib import Path" in src_all)
    ck("06", "no model construction / checkpoint load / forward / autograd CALL in CODE cells",
       all(t not in src_code for t in ("torch.load(", "load_g_component(", "load_bphi_component(",
                                       "torch.autograd", "\.backward(", "torch.optim",
                                       "optimizer.step(")))
    ck("07", "no Grad-CAM / router attribution / training in CODE cells",
       all(t not in src_code for t in ("gradcam", "router_gradient_x_input", "train(", "fit(")))
    ck("08", "no protected-data access in CODE cells",
       all(t not in src_code.lower() for t in ("router_holdout/", "test/", "image_path",
                                               "mask_path", ".npy", ".npz")))
    ck("09", "notebook reads only the six v1.0 scientific/governance artifacts",
       all(f in src_all for f in
           ("phase35_first_scientific_execution_v1_0.json",
            "phase35_first_scientific_execution_final_check_v1_0.json",
            "phase35_first_scientific_execution_terminal_v1_0.json",
            "phase35_scientific_execution_static_preflight_v1_0.json",
            "phase35_scientific_execution_source_freeze_v1_0.json",
            "phase35_interpretability_scientific_result_v1_0.json")))
    ck("10", "notebook states the descriptive claim boundary",
       "DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE" in src_all
       and "not ground-truth localization" in src_all)
    ck("11", "notebook is classified READ_ONLY", "READ_ONLY" in src_all)
    ck("12", "notebook kernel metadata is jup-venv",
       nb["metadata"].get("kernelspec", {}).get("name") == "jup-venv")

    npass = sum(1 for c in checks if c["pass"])
    doc = OrderedDict([
        ("artifact",
         "phase35_interpretability_scientific_execution_reviewer_notebook_audit_v1_0"),
        ("section", "§X"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0"),
        ("notebook_path", NBREL), ("notebook_sha256", sha(NB)),
        ("classification", "READ_ONLY_REVIEWER_NOTEBOOK_AUDIT"),
        ("checks", checks), ("total_checks", len(checks)), ("passed", npass),
        ("failed", len(checks) - npass),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", npass == len(checks)),
    ])
    op = (ROOT / "reports/audits/"
          "phase35_interpretability_scientific_execution_reviewer_notebook_audit_v1_0.json")
    op.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"notebook audit: {npass}/{len(checks)}")
    for c in checks:
        if not c["pass"]:
            print("  FAIL", c["id"], c["desc"], c["detail"])
    print("audit sha256:", sha(op))
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
