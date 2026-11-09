"""ReMedFiLM V9 -- post-export verification (read-only, no science).

Checks the delivered DOCX and PDF against the V9 registry and the build
manifest, and renders every PDF page to catch blank or clipped pages.
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf
from docx import Document

ROOT = Path(__file__).resolve().parents[3]
FDR = ROOT / "full_doc_report"
DOCX = FDR / "ReMedFiLM_Complete_Scientific_Report_V9.docx"
PDF = FDR / "ReMedFiLM_Complete_Scientific_Report_V9.pdf"
MANIFEST = FDR / "V9" / "V9_FINAL_REPORT_MANIFEST.json"
REGISTRY = FDR / "REMEDFILM_V9_RESULTS_REGISTRY.json"
RENDER_DIR = FDR / "V9" / "v9_build" / ".render_v9"

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def report() -> int:
    failed = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    return 0 if not failed else 1


def main() -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    met = {m["metric_id"]: m["value"] for m in reg["metrics"]}

    check("DOCX exists", DOCX.exists(), str(DOCX))
    check("PDF exists", PDF.exists(), str(PDF))
    if not (DOCX.exists() and PDF.exists()):
        return report()

    check("DOCX non-empty", DOCX.stat().st_size > 1_000_000,
          f"{DOCX.stat().st_size:,} bytes")
    check("PDF non-empty", PDF.stat().st_size > 100_000,
          f"{PDF.stat().st_size:,} bytes")

    doc = Document(DOCX)
    texts = "\n".join(p.text for p in doc.paragraphs)
    tables_text = "\n".join(
        c.text for t in doc.tables for row in t.rows for c in row.cells
    )
    all_text = texts + "\n" + tables_text

    check("DOCX parses", True,
          f"{len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables")
    check("inline images >= 34", len(doc.inline_shapes) >= 34,
          f"{len(doc.inline_shapes)} inline images")

    fig_caps = [
        p.text for p in doc.paragraphs
        if p.style and p.style.name == "Caption" and p.text.startswith("Figure ")
    ]
    tab_caps = [
        p.text for p in doc.paragraphs
        if p.style and p.style.name == "Caption" and p.text.startswith("Table ")
    ]
    fnum = [int(re.match(r"Figure (\d+)\.", t).group(1)) for t in fig_caps]
    tnum = [int(re.match(r"Table (\d+)\.", t).group(1)) for t in tab_caps]
    check("figure numbering sequential", fnum == list(range(1, len(fnum) + 1)), str(fnum))
    check("table numbering sequential", tnum == list(range(1, len(tnum) + 1)), str(tnum))
    # 33 inherited figures + 1 conceptual infographic; 14 captioned tables
    # (the remaining Word tables are shaded note boxes, not numbered tables).
    check("figure count == 34", len(fig_caps) == 34, f"{len(fig_caps)} captions")
    check("table count == 14", len(tab_caps) == 14, f"{len(tab_caps)} captions")
    check("word tables (incl. note boxes) >= 26", len(doc.tables) >= 26,
          f"{len(doc.tables)}")

    fig_c = next((t for t in fig_caps if "Conceptual reference schematic" in t), "")
    check("conceptual infographic is a numbered figure",
          bool(fig_c), fig_c[:110])
    check("conceptual infographic carries the implementation caveat",
          "ASPIRATIONAL" in fig_c
          and "B_HISTORICAL_OFFLINE_CACHED_CANDIDATE_REPLAY" in fig_c, "")
    check("conceptual infographic is Figure 6 (reading order)",
          fig_c.startswith("Figure 6."), fig_c[:40])
    check("verified methodology figure is Figure 2",
          any(t.startswith("Figure 2.") and "Code-verified" in t for t in fig_caps), "")

    integ = [
        ("EFF_A8_VAL808_CONDITIONAL_GMAC",
         f"{float(met['EFF_A8_VAL808_CONDITIONAL_GMAC']):.4f}"),
        ("EFF_A8_HOLDOUT_CONDITIONAL_GMAC",
         f"{float(met['EFF_A8_HOLDOUT_CONDITIONAL_GMAC']):.4f}"),
    ]
    for mid, printed in integ:
        check(f"registry value printed: {mid}", printed in all_text, printed)

    canon = reg["canonical_result"]
    check("canonical FULL macro Dice printed",
          f"{canon['full_macro_dice']:.6f}"[:7] in all_text,
          f"{canon['full_macro_dice']:.6f}")
    check("canonical G macro Dice printed",
          f"{canon['global_macro_dice']:.6f}"[:7] in all_text,
          f"{canon['global_macro_dice']:.6f}")

    check("FULL identified as the 4-component system",
          "G + R_psi + B_phi + S_omega" in all_text, "")
    check("backbone explicitly demoted",
          "backbone and a legitimate ablation baseline" in all_text
          or "GlobalMedFiLM is the `G` backbone" in all_text, "")

    check("HAM10000 disposition disclosed",
          "EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED"
          in all_text, "")
    check("Mode-B inference class disclosed",
          "B_HISTORICAL_OFFLINE_CACHED_CANDIDATE_REPLAY" in all_text, "")
    check("TEST1683 historical access disclosed",
          "Phase-39" in all_text or "Phase 39" in all_text, "")
    check("registry size matches registry",
          f"{reg['metric_count']} records" in all_text, str(reg["metric_count"]))
    check("references section present",
          any(p.text.strip() == "References" for p in doc.paragraphs), "")

    residual = re.findall(r"\bV8\b", all_text)
    check("no residual V8 self-reference", len(residual) == 0,
          f"{len(residual)} token(s)")

    hdr = " ".join(p.text for s in doc.sections for p in s.header.paragraphs)
    check("running header says V9", "V9" in hdr and "V8" not in hdr,
          hdr.strip()[:80])

    # every REMEDFILM_*/ReMedFiLM_* artifact the report cites must exist
    cited = set(re.findall(
        r"(?:REMEDFILM|ReMedFiLM)_[A-Za-z0-9_./-]*\.(?:csv|json|md|png|pdf|py|ps1)",
        all_text,
    ))
    search_roots = [
        FDR, FDR / "V9", FDR / "tables", FDR / "figures", FDR / "V9" / "figures",
        FDR / "V9" / "v9_build", ROOT, ROOT / "reports" / "tables",
    ]
    absent = sorted(
        n for n in cited
        if not any((r / n).exists() for r in search_roots)
    )
    check("all cited report artifacts exist", not absent,
          f"{len(cited)} cited; missing={absent}")

    pdf = pymupdf.open(PDF)
    check("PDF opens", True, f"{len(pdf)} pages")
    check("PDF page count >= 26", len(pdf) >= 26, str(len(pdf)))
    page_texts = [pg.get_text("text") for pg in pdf]
    check("every page has extractable text",
          all(t.strip() for t in page_texts),
          ",".join(str(i + 1) for i, t in enumerate(page_texts) if not t.strip()))

    joined = "\n".join(page_texts)
    for probe in (
        "Overview and contributions",
        "Methodology",
        "External retrospective evaluation",
        "Component progression and ablation",
        "Computational complexity",
        "Conclusions, limitations",
        "References",
    ):
        check(f"PDF section present: {probe}", probe in joined, "")

    check("PDF contains HAM10000 disclosure", "HAM10000" in joined, "")
    check("PDF contains Figure 3 caption",
          "Conceptual reference schematic" in joined, "")
    check("PDF contains VAL808 conditional compute",
          f"{float(met['EFF_A8_VAL808_CONDITIONAL_GMAC']):.4f}" in joined, "")

    img_pages = sum(1 for pg in pdf if pg.get_images(full=True))
    check("PDF has >= 20 image-bearing pages", img_pages >= 20, str(img_pages))
    # every one of the 34 figures must survive into the PDF
    pdf_images = sum(len(pg.get_images(full=True)) for pg in pdf)
    check("PDF carries >= 34 embedded images", pdf_images >= 34, str(pdf_images))

    near_blank = []
    for i, pg in enumerate(pdf, start=1):
        txt = pg.get_text("text").strip()
        n_img = len(pg.get_images(full=True))
        if len(txt) < 40 and n_img == 0:
            near_blank.append((i, len(txt), n_img))
    check("no near-blank pages", len(near_blank) == 0, str(near_blank))

    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    rendered = 0
    for i, pg in enumerate(pdf, start=1):
        pix = pg.get_pixmap(dpi=100)
        if pix.width > 0 and pix.height > 0:
            pix.save(str(RENDER_DIR / f"page_{i:03d}.png"))
            rendered += 1
    check("all pages rendered", rendered == len(pdf), f"{rendered}/{len(pdf)}")

    check("manifest figure count matches DOCX",
          man["counts"]["figures"] == len(fig_caps),
          f"{man['counts']['figures']} vs {len(fig_caps)}")
    check("manifest table count matches DOCX",
          man["counts"]["tables"] == len(tab_caps),
          f"{man['counts']['tables']} vs {len(tab_caps)}")
    check("manifest registry count matches registry",
          man["registry_metric_count"] == reg["metric_count"], "")

    return report()


if __name__ == "__main__":
    sys.exit(main())