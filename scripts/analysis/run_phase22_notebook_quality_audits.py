"""Phase 22 reviewer notebook — §10 table coverage and §11 execution quality.

Both audits read the ACTUAL notebook bytes and the persisted Phase-22 tables.
They perform NO inference and touch NO TEST data.

Outputs (folded into the after-repair report and the determinism report):
  reports/audits/phase22_notebook_table_coverage.json
  reports/audits/phase22_notebook_execution_quality.json
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import nbformat

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports/audits"
TAB = ROOT / "reports/tables"
NB_PATH = ROOT / "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb"

# §10 — tables whose content must be VISIBLE in the notebook (not hidden behind
# prose). Grouped by the requirement that motivates them.
REQUIRED_TABLES = {
    "gt_free_proxy_vs_benefit": "reports/tables/phase22_gt_free_proxy_vs_benefit.csv",
    "gt_aware_posthoc_associations":
        "reports/tables/phase22_gt_aware_posthoc_associations.csv",
    "scale_sensitivity": "reports/tables/phase22_scale_sensitivity.csv",
    "scale_sensitivity_by_domain":
        "reports/tables/phase22_scale_sensitivity_by_domain.csv",
    "regional_intervention_per_image":
        "reports/tables/phase22_regional_intervention_per_image.csv",
    "harm_analysis": "reports/tables/phase22_harm_analysis.csv",
    "benefit_heterogeneity": "reports/tables/phase22_benefit_heterogeneity.csv",
    "routing_regret": "reports/tables/phase22_routing_regret.csv",
    "resource_frontier": "reports/tables/phase22_resource_frontier.csv",
    "conditional_compute_envelopes":
        "reports/tables/phase22_conditional_compute_envelopes.csv",
    "kub_tiny_analysis": "reports/tables/phase22_kub_tiny_analysis.csv",
    "global_failure_atlas": "reports/tables/phase22_global_failure_atlas.csv",
    "roi_geometry": "reports/tables/phase22_roi_geometry.csv",
    "prediction_derived_roi": "reports/tables/phase22_prediction_derived_roi.csv",
    "domain_preservation": "reports/tables/phase22_domain_preservation.csv",
    "statistics": "reports/tables/phase22_statistics.csv",
    "cpu_baseline": "reports/tables/phase22_cpu_baseline.csv",
}


def _nb_text(nb) -> str:
    parts = []
    for cell in nb.cells:
        src = cell.get("source", "")
        s = "".join(src) if isinstance(src, list) else str(src)
        s = re.sub(r"^\s*>\s?", "", s, flags=re.M)
        s = re.sub(r'"\s*\n\s*"', "", s)
        s = re.sub(r"'\s*\n\s*'", "", s)
        s = re.sub(r"\s+", " ", s)
        parts.append(s)
    return " ".join(parts)


def _out_text(nb) -> str:
    parts = []
    for cell in nb.cells:
        for o in cell.get("outputs", []) or []:
            d = o.get("data", {})
            if not isinstance(d, dict):
                continue
            for k in ("text/plain", "text/html", "text/markdown"):
                if k in d:
                    v = d[k]
                    parts.append(" ".join(v) if isinstance(v, list) else str(v))
            t = o.get("text")
            if t:
                parts.append("".join(t) if isinstance(t, list) else str(t))
    return re.sub(r"\s+", " ", " ".join(parts))


def _unrefuted(text: str, claim_pat: str, refute_pat: str) -> bool:
    """True only if a stale claim appears WITHOUT a refutation nearby."""
    for m in re.finditer(claim_pat, text, re.I):
        ctx = text[max(0, m.start() - 300):m.end() + 300]
        if not re.search(refute_pat, ctx, re.I):
            return True
    return False


def main() -> int:
    raw = NB_PATH.read_bytes()
    nb = nbformat.reads(raw.decode("utf-8"), as_version=4)
    nb_sha = hashlib.sha256(raw).hexdigest()
    src = _nb_text(nb)
    outs = _out_text(nb)

    # ---- §10 table coverage ---------------------------------------------- #
    cov = []
    for key, rel in REQUIRED_TABLES.items():
        name = Path(rel).name
        p = ROOT / rel
        exists = p.exists()
        rows = None
        if exists:
            rows = sum(1 for _ in p.open(encoding="utf-8")) - 1
        # Visible if the table is read in code AND something about it is printed
        # or displayed (we cannot map a Styler back to its file, so require the
        # file name to appear in the code AND a display/sty/print nearby).
        mentioned = name.replace(".csv", "") in src or name in src
        displayed = bool(re.search(
            re.escape(name.replace(".csv", "")) + r"[^\n]{0,200}?(sty|display|print)",
            src)) or (name in src and "display(" in src)
        cov.append({"table": key, "path": rel, "exists": exists,
                    "rows": rows, "referenced_in_code": mentioned,
                    "appears_displayed": displayed})
    missing = [c["table"] for c in cov if not c["exists"]]
    not_shown = [c["table"] for c in cov if c["exists"] and not c["referenced_in_code"]]

    html_tables = sum(1 for c in nb.cells if c.get("cell_type") == "code"
                      for o in c.get("outputs", [])
                      if "text/html" in (o.get("data", {}) or {}))

    coverage = {
        "artifact": "phase22_notebook_table_coverage",
        "phase": 22,
        "notebook_sha256": nb_sha,
        "required_tables": len(REQUIRED_TABLES),
        "tables_present_on_disk": sum(1 for c in cov if c["exists"]),
        "tables_referenced_in_notebook": sum(1 for c in cov if c["referenced_in_code"]),
        "tables_absent": missing,
        "tables_not_referenced": not_shown,
        "html_table_outputs": html_tables,
        "gt_free_proxy_table_visible":
            any(c["table"] == "gt_free_proxy_vs_benefit" and c["referenced_in_code"]
                for c in cov),
        "gt_aware_posthoc_table_visible":
            any(c["table"] == "gt_aware_posthoc_associations" and c["referenced_in_code"]
                for c in cov),
        "per_table": cov,
        "verdict": "PASS" if (not missing and not not_shown
                              and html_tables >= 15) else "FAIL",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase22_notebook_table_coverage.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- §11 execution quality ------------------------------------------- #
    code_cells = [c for c in nb.cells if c.get("cell_type") == "code"]
    executed = [c for c in code_cells if c.get("execution_count") is not None]
    counts = [c.get("execution_count") for c in executed]
    monotonic = all(counts[i] < counts[i + 1] for i in range(len(counts) - 1))
    errors = [{"cell_index": ci, "ename": o.get("ename"),
               "evalue": (o.get("evalue") or "")[:200]}
              for ci, c in enumerate(nb.cells) for o in c.get("outputs", [])
              if o.get("output_type") == "error"]
    stderr_outputs = sum(1 for c in nb.cells for o in c.get("outputs", [])
                         if o.get("output_type") == "stream" and o.get("name") == "stderr")

    # --- exact wording requirements --------------------------------------- #
    req = {
        "512 wording (not globally optimal)":
            bool(re.search(r"does not establish a globally optimal", outs + " " + src, re.I)),
        "KUB TINY CI includes zero":
            bool(re.search(r"CI.{0,80}includes zero", outs + " " + src, re.I)),
        "KUB TINY descriptive only":
            bool(re.search(r"descriptive and not\s*statistically established", outs, re.I)),
        "GT-free separation stated":
            bool(re.search(r"GT-free", src, re.I) and re.search(r"deployable", src, re.I)),
    }
    stale = {
        "stale 'deployable recall' claim":
            _unrefuted(outs + " " + src,
                       r"recall[^\n]{0,60}?(?:best|top)[^\n]{0,25}?deployable",
                       r"invalid|no longer|not deployable|requires (the )?ground"
                       r"|cannot be computed"),
        "stale '512 is optimal' claim":
            (bool(re.search(r"\b512\b[^\n]{0,40}(is )?(globally )?optimal", src, re.I))
             and "does not establish a globally optimal" not in (outs + " " + src)),
        "stale KUB TINY significance claim":
            _unrefuted(outs + " " + src,
                       r"TINY[^\n]{0,60}improve[sd]?[^\n]{0,40}(significant|established)",
                       r"not\s+statistically established|descriptive|includes zero"),
    }

    quality = {
        "artifact": "phase22_notebook_execution_quality",
        "phase": 22,
        "notebook_sha256": nb_sha,
        "total_code_cells": len(code_cells),
        "executed_code_cells": len(executed),
        "all_code_cells_executed": len(executed) == len(code_cells),
        "execution_counts": counts,
        "execution_counts_monotonic": monotonic,
        "error_outputs": len(errors),
        "error_detail": errors,
        "stderr_stream_outputs": stderr_outputs,
        "required_wording": req,
        "required_wording_all_present": all(req.values()),
        "stale_claims": stale,
        "stale_claims_all_absent": not any(stale.values()),
        "image_png_outputs": sum(1 for c in code_cells for o in c.get("outputs", [])
                                 if "image/png" in (o.get("data", {}) or {})),
        "verdict": "PASS" if (len(executed) == len(code_cells) and monotonic
                              and not errors and all(req.values())
                              and not any(stale.values())) else "FAIL",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase22_notebook_execution_quality.json").write_text(
        json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")

    print("§10 table coverage:", coverage["verdict"],
          "| present", coverage["tables_present_on_disk"],
          "| referenced", coverage["tables_referenced_in_notebook"],
          "| html tables", html_tables,
          "| gt-free visible", coverage["gt_free_proxy_table_visible"],
          "| gt-aware visible", coverage["gt_aware_posthoc_table_visible"])
    print("§11 execution quality:", quality["verdict"],
          "| code", f"{len(executed)}/{len(code_cells)}",
          "| monotonic", monotonic, "| errors", len(errors),
          "| wording", all(req.values()), "| stale absent", not any(stale.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
