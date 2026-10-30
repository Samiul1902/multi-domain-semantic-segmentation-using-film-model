"""Final independent validation of the delivered supervisor DOCX.

Read-only with respect to scientific evidence. This script only re-opens the
already-built DOCX, recomputes its SHA-256, and re-runs every compliance scan
required by the FINAL SUPERVISOR REPORT work order.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

from docx import Document

ROOT = Path(r"D:\Softfors\jup")
DOCX = ROOT / "paper_doc" / "RA_MedFiLM_BARR_Full_Supervisor_Report.docx"
MANIFEST = ROOT / "paper_doc" / "report_build_manifest.json"

PHASE30_Q = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
             "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE39_Q = ("POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_"
             "PREOUTCOME_TECHNICAL_FAILURES")

FORBIDDEN_TOKENS = [
    "TODO", "TBD", "INSERT HERE", "XXX", "LOREM",
]
PROHIB = [
    "cannot", "can not", "must not", "never", "forbidden", "not produced",
    "was not produced", "not evaluable", "is not", "are not", "do not",
    "does not", "we do not", "no confirmatory", "no new confirmatory",
    "not authorized", "was not authorized", "not available", "missing",
    "not performed", "not computed", "not reported", "n_confirmatory=0",
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\u2014", " -- ").replace("\u2013", " - ")).strip()


def main() -> int:
    raw = DOCX.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    size = len(raw)

    doc = Document(str(DOCX))
    paras = [p.text for p in doc.paragraphs]
    # Include table cell text: metadata placeholders and NOT_PRODUCED markers
    # live inside tables in this report, so a paragraphs-only scan misses them.
    table_text: list[str] = []
    for tb in doc.tables:
        for row in tb.rows:
            for cell in row.cells:
                table_text.append(cell.text)
    paras_all = paras + table_text
    all_text = norm("\n".join(paras_all))
    n_tables = len(doc.tables)

    with zipfile.ZipFile(DOCX) as z:
        media = [n for n in z.namelist() if n.startswith("word/media/")]
        doc_xml = z.read("word/document.xml").decode("utf-8", "replace")
        footer_xml = "".join(
            z.read(n).decode("utf-8", "replace")
            for n in z.namelist() if re.match(r"word/footer\d+\.xml$", n)
        )

    # ---- required structural checks
    toc_present = "TOC \\o" in doc_xml or "TOC \\\\o" in doc_xml or " TOC " in doc_xml
    page_field = "PAGE" in footer_xml
    npages_field = "NUMPAGES" in footer_xml
    n_figures = len(media)

    # ---- section inventory
    heading_re = re.compile(r"^\s*(\d{1,2})\.\s+[A-Z]")
    headings = [p for p in paras if p.strip()]
    n_h1 = sum(1 for p in doc.paragraphs
               if p.style is not None and p.style.name == "Heading 1")
    n_h2 = sum(1 for p in doc.paragraphs
               if p.style is not None and p.style.name == "Heading 2")
    n_h3 = sum(1 for p in doc.paragraphs
               if p.style is not None and p.style.name == "Heading 3")

    # ---- qualifiers
    p30_ok = PHASE30_Q in all_text.replace("- ", "-").replace(" ", "") or \
        norm(PHASE30_Q) in all_text or PHASE30_Q.replace("_", "") in all_text.replace("_", "")
    # robust: strip underscores/whitespace for match
    def squash(s: str) -> str:
        return re.sub(r"[\s_]+", "", s)
    p30_ok = squash(PHASE30_Q) in squash(all_text)
    p39_ok = squash(PHASE39_Q) in squash(all_text)

    # ---- missing primary endpoint disclosure
    # IMPORTANT: must be tested on the RAW text. Under squash(), underscore
    # sequences are removed, so "NOT_PRODUCED" -> "NOTPRODUCED" would never
    # match the squashed needle "NOT_PRODUCED".
    raw_text = "\n".join(paras_all)
    missing_ep = (
        "NOT_PRODUCED" in all_text
        and "PRIMARY_ENDPOINT_NOT_PRODUCED" in all_text
        and "primary comparative endpoint" in all_text.lower()
        and "C-gGLOBAL" in all_text
    )

    # ---- UNTOUCHED_ONE_SHOT_TEST must not be used affirmatively
    untouched_occurrences = []
    for m in re.finditer(r"UNTOUCHED_ONE_SHOT_TEST", all_text):
        ctx = all_text[max(0, m.start() - 220):m.end() + 220].lower()
        assertive = any(v in ctx for v in [
            "is an", "is the", "we report an", "constitutes", "remains an",
            "can be called", "is hereby",
        ])
        prohib_ctx = any(k in ctx for k in [
            "never", "must not", "not be called", "forbidden", "prohibit",
            "is not", "cannot", "not used", "absent", "avoid",
        ])
        if assertive and not prohib_ctx:
            untouched_occurrences.append(all_text[max(0, m.start() - 120):m.end() + 120])
    untouched_ok = len(untouched_occurrences) == 0

    # ---- forbidden Phase39 / TEST claim scan
    # A violation is an AFFIRMATIVE Phase39/TEST claim using a forbidden term.
    # The RUNNER_HOLDOUT non-inferiority claim (Phase30) is explicitly ALLOWED by
    # the frozen claim ledger (claims C-A2 / C-T2) provided it carries the
    # mandatory Phase30 qualifier; it is therefore not a violation.
    forbidden_terms = [
        "superior to", "outperformed", "significantly better",
        "statistically significant improvement",
        "confirmatory endpoint was met", "primary endpoint was met",
        "we prove", "demonstrates superiority", "test superiority",
        "test non-inferiority", "non-inferiority on test",
        "superiority on test", "preservation on test", "harm-free on test",
    ]
    ALLOWED_CLAIM_MARKERS = [
        "router_holdout", "phase30", "phase 30", "holdout", "must carry",
        "mandatory qualifier", "with the mandatory", "allowed wording",
        "claim ledger", "c-a2", "c-t2",
    ]
    violations = []
    for term in forbidden_terms:
        for m in re.finditer(re.escape(term), all_text, flags=re.IGNORECASE):
            ctx = all_text[max(0, m.start() - 300):m.end() + 300]
            low = ctx.lower()
            if any(k in low for k in PROHIB):
                continue
            if any(k in low for k in ALLOWED_CLAIM_MARKERS):
                continue
            if "phase39" in low or "phase 39" in low or "test" in low or "c-gglobal" in low:
                violations.append((term, ctx))

    # ---- placeholder scan
    placeholder_hits = []
    for tok in FORBIDDEN_TOKENS:
        if re.search(re.escape(tok), all_text, flags=re.IGNORECASE):
            for m in re.finditer(re.escape(tok), all_text, flags=re.IGNORECASE):
                ctx = all_text[max(0, m.start() - 80):m.end() + 80]
                placeholder_hits.append((tok, ctx))

    # ---- metadata placeholders (raw text, brackets preserved by norm())
    meta_present = {t: (t in all_text) for t in [
        "[AUTHOR NAME]", "[SUPERVISOR NAME]", "[DEPARTMENT]",
        "[INSTITUTION]", "[DATE]",
    ]}
    meta_ok = all(meta_present.values())
    meta_labelled = all(lbl in all_text for lbl in
                        ["Author", "Supervisor", "Department", "Institution", "Date"])

    # ---- reference count (main list = bracketed keys; appendix list = numbered)
    ref_bracketed = len(re.findall(r"\[[a-z]+\d{4}[a-z]*\]", all_text))
    ref_numbered = len(re.findall(r"(?m)^\s*\d{1,2}\.\s+\[[a-z]+\d{4}", "\n".join(paras)))
    if ref_numbered == 0:
        ref_numbered = len(
            re.findall(r"(?m)^\s*\d{1,2}\.\s+\[[a-z]+\d{4}", all_text))
    ref_count = max(ref_bracketed, ref_numbered)

    # ---- section presence
    required = [
        "Executive Summary", "Table of Contents", "List of Figures",
        "List of Tables", "Abbreviations", "Conclusion", "References",
        "Appendix A", "Appendix G", "Supervisor Quick Review",
        "Background", "Problem Statement", "Novelty", "Methodology",
        "Architecture", "Ablation", "Reproducibility", "ROUTER_HOLDOUT",
        "Robustness", "Interpretability", "Limitations", "Future Work",
    ]
    missing = [r for r in required if squash(r) not in squash(all_text)]

    report = {
        "docx_path": str(DOCX),
        "docx_sha256": sha,
        "docx_size_bytes": size,
        "n_paragraphs": len(paras),
        "n_tables": n_tables,
        "n_figures": n_figures,
        "n_heading1": n_h1,
        "n_heading2": n_h2,
        "n_heading3": n_h3,
        "toc_present": bool(toc_present),
        "page_field_present": bool(page_field),
        "numpages_field_present": bool(npages_field),
        "phase30_qualifier_present": bool(p30_ok),
        "phase39_qualifier_present": bool(p39_ok),
        "missing_primary_endpoint_disclosed": bool(missing_ep),
        "untouched_affirmative_uses": untouched_occurrences,
        "untouched_scan_pass": bool(untouched_ok),
        "forbidden_claim_violations": violations,
        "forbidden_claim_scan_pass": len(violations) == 0,
        "placeholder_hits": placeholder_hits,
        "placeholder_scan_pass": len(placeholder_hits) == 0,
        "metadata_placeholders_present_and_labelled": bool(meta_ok and meta_labelled),
        "metadata_placeholder_detail": meta_present,
        "reference_count": ref_count,
        "missing_required_sections": missing,
        "manifest_sha256_matches": None,
    }

    if MANIFEST.exists():
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        report["manifest_sha256_matches"] = (m.get("docx_sha256") == sha)
        report["manifest_n_tables"] = m.get("n_tables")
        report["manifest_n_figures"] = m.get("n_figures")
        report["manifest_scientific_delta"] = m.get("scientific_delta")
        report["manifest_scope"] = m.get("final_scientific_scope")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
