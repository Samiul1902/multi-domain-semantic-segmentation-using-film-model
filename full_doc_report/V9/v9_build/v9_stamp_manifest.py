"""ReMedFiLM V9 -- stamp the export results into the build manifest.

Run AFTER the PDF has been exported. Reads the delivered DOCX and PDF from
disk, records their real sizes, hashes and page count in
``V9_FINAL_REPORT_MANIFEST.json``, and asserts the PDF was built from the DOCX
that is actually being delivered.

Read-only with respect to the DOCX/PDF. No training, no inference.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
FDR = ROOT / "full_doc_report"
DOCX = FDR / "ReMedFiLM_Complete_Scientific_Report_V9.docx"
PDF = FDR / "ReMedFiLM_Complete_Scientific_Report_V9.pdf"
MANIFEST = FDR / "V9" / "V9_FINAL_REPORT_MANIFEST.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    for p in (DOCX, PDF, MANIFEST):
        if not p.exists():
            print(f"MISSING: {p}")
            return 1

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))

    docx_sha = sha256(DOCX)
    if man.get("docx_sha256") != docx_sha:
        print("DOCX hash does not match the manifest build record -- "
              "re-export the PDF and re-run this step")
        print("  manifest:", man.get("docx_sha256"))
        print("  on disk :", docx_sha)
        return 1

    with pymupdf.open(PDF) as pdf:
        pages = len(pdf)
        text = "".join(pg.get_text("text") for pg in pdf)

    required = [
        "Conceptual reference schematic",
        "EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED",
        "B_HISTORICAL_OFFLINE_CACHED_CANDIDATE_REPLAY",
        "32.6673",
        "References",
    ]
    missing = [r for r in required if r not in text]
    if missing:
        print(f"PDF does not reflect the corrected DOCX: missing {missing}")
        return 1

    man["pdf"] = PDF.relative_to(ROOT).as_posix()
    man["pdf_bytes"] = PDF.stat().st_size
    man["pdf_pages"] = pages
    man["pdf_sha256"] = sha256(PDF)
    man["pdf_contains_corrected_content"] = True
    MANIFEST.write_text(
        json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"manifest stamped: pdf_pages={pages} pdf_bytes={man['pdf_bytes']:,}")
    print(f"docx_sha256={docx_sha}")
    print(f"pdf_sha256 ={man['pdf_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())