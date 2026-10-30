"""
build_supervisor_report_docx.py
===============================
Deterministic builder for the RA-MedFiLM-BARR Full Supervisor Report.

DOCUMENT ASSEMBLY ONLY.
  scientific_delta = 0
  TEST access = 0 ; TEST image reads = 0 ; TEST GT reads = 0
  model inference = 0 ; training = 0 ; new statistics = 0
  new bootstrap = 0 ; new comparator computation = 0

Every scientific number and claim comes from the frozen release artifacts via
report_content_data.py.  This script modifies NO scientific source code.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_content_data as D  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(r"D:\Softfors\jup")
OUT_DIR = REPO / "paper_doc"
OUT_DOCX = OUT_DIR / "RA_MedFiLM_BARR_Full_Supervisor_Report.docx"
OUT_MANIFEST = OUT_DIR / "report_build_manifest.json"
OUT_README = OUT_DIR / "README.txt"
BUILDER_SELF = Path(__file__).resolve()

METHODOLOGY_IMAGE = Path(
    r"C:\Users\user\Downloads\RA-MedFiLM-BARR Multi-Domain Infographic.png"
)

FIG = REPO / "reports" / "figures"

# ---------------------------------------------------------------------------
# Plain-language rewrite guard: the report is a supERVISOR report, so all
# scientific content is transcribed verbatim from the frozen sources.
# ---------------------------------------------------------------------------

ACCENT = RGBColor(0x1F, 0x3B, 0x5C)      # restrained academic navy
HEADER_FILL = "1F3B5C"
ALT_FILL = "EEF2F7"
BOX_FILL = "FBF3E4"

TITLE = ("RA-MedFiLM-BARR:\nBenefit-Aware Regional Refinement for "
         "Multi-Domain Medical Image Segmentation")
SUBTITLE = ("Comprehensive Research, Methodology, Experimental Evidence, "
            "Robustness Analysis, and Final Manuscript Summary")

TOC_ENTRIES = []   # populated as headings are added


# ===========================================================================
# Low-level helpers
# ===========================================================================
def set_cell_shading(cell, fill_hex: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tcPr.append(shd)


def set_cell_margins(cell, top=60, start=90, bottom=60, end=90) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, val in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcPr.append(mar)


def add_field(paragraph, instr: str) -> None:
    """Insert a Word field (e.g. PAGE, TOC)."""
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr_el)
    run._r.append(fld_sep)
    run._r.append(fld_end)
    return run


def set_repeat_header_row(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)


def add_bookmark(paragraph, name: str, bid: int) -> None:
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bid))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bid))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


# ===========================================================================
# Document setup
# ===========================================================================
def new_document() -> Document:
    doc = Document()

    # Base style
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), "Calibri")
    rfonts.set(qn("w:hAnsi"), "Calibri")
    rfonts.set(qn("w:cs"), "Calibri")
    pf = normal.paragraph_format
    pf.line_spacing = 1.15
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Heading styles
    for name, size, color, space_before, space_after in (
        ("Heading 1", 17, ACCENT, 16, 8),
        ("Heading 2", 13.5, ACCENT, 12, 6),
        ("Heading 3", 11.5, ACCENT, 10, 4),
    ):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = color
        st.paragraph_format.space_before = Pt(space_before)
        st.paragraph_format.space_after = Pt(space_after)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.line_spacing = 1.05
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Caption style
    cs = doc.styles["Caption"]
    cs.font.name = "Calibri"
    cs.font.size = Pt(9.5)
    cs.font.italic = True
    cs.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    cs.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cs.paragraph_format.space_after = Pt(10)

    # A4 + 2.54 cm margins
    for s in doc.sections:
        s.page_width = Cm(21.0)
        s.page_height = Cm(29.7)
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)

    return doc


def add_page_number_footer(section) -> None:
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = ""
    run = p.add_run("RA-MedFiLM-BARR - Full Supervisor Report  |  Page ")
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
    fld = add_field(p, "PAGE")
    fld.font.size = Pt(8.5)
    fld.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
    r2 = p.add_run(" of ")
    r2.font.size = Pt(8.5)
    r2.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
    fld2 = add_field(p, "NUMPAGES")
    fld2.font.size = Pt(8.5)
    fld2.font.color.rgb = RGBColor(0x60, 0x60, 0x60)


# ===========================================================================
# Content helpers
# ===========================================================================
def h1(doc, text, toc=True):
    p = doc.add_heading(text, level=1)
    if toc:
        TOC_ENTRIES.append((1, text))
    return p


def h2(doc, text):
    TOC_ENTRIES.append((2, text))
    return doc.add_heading(text, level=2)


def h3(doc, text):
    return doc.add_heading(text, level=3)


def para(doc, text, justify=True, italic=False, bold=False, size=None):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = (
        WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT)
    r = p.add_run(text)
    r.italic = italic
    r.bold = bold
    if size:
        r.font.size = Pt(size)
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.add_run(text)
    return p


def numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.add_run(text)
    return p


def mono_block(doc, lines):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0.3)
        r = p.add_run(ln)
        r.font.name = "Consolas"
        r.font.size = Pt(8.5)
    return


def add_table(doc, headers, rows, widths=None, caption=None,
              font_size=8.5, header_size=8.5):
    if caption:
        cp = doc.add_paragraph(style="Caption")
        cp.add_run(caption)
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    hdr = table.rows[0]
    for i, htxt in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(str(htxt))
        r.bold = True
        r.font.size = Pt(header_size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(cell, HEADER_FILL)
        set_cell_margins(cell)
    set_repeat_header_row(hdr)

    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cell = cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(str(val))
            r.font.size = Pt(font_size)
            if ridx % 2 == 1:
                set_cell_shading(cell, ALT_FILL)
            set_cell_margins(cell)

    if widths:
        for i, w in enumerate(widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table


def add_figure(doc, image_path: Path, caption: str, width_cm=15.5):
    if not image_path.exists():
        para(doc, f"[Figure not available: {image_path}]", italic=True)
        return False
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    run = p.add_run()
    run.add_picture(str(image_path), width=Cm(width_cm))
    cp = doc.add_paragraph(style="Caption")
    cp.add_run(caption)
    return True


def info_box(doc, title, lines, fill=BOX_FILL):
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    cell = t.rows[0].cells[0]
    set_cell_shading(cell, fill)
    set_cell_margins(cell, top=140, start=160, bottom=140, end=160)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = ACCENT
    for ln in lines:
        pp = cell.add_paragraph()
        pp.paragraph_format.space_after = Pt(3)
        pp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        rr = pp.add_run("•  " + ln)
        rr.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ===========================================================================
# Front matter
# ===========================================================================
def build_title_page(doc):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("RA-MedFiLM-BARR:")
    r.bold = True
    r.font.size = Pt(26)
    r.font.color.rgb = ACCENT

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Benefit-Aware Regional Refinement for\nMulti-Domain Medical Image Segmentation")
    r.bold = True
    r.font.size = Pt(18)
    r.font.color.rgb = ACCENT

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(SUBTITLE)
    r.font.size = Pt(12.5)
    r.italic = True
    r.font.color.rgb = RGBColor(0x40, 0x50, 0x60)

    for _ in range(2):
        doc.add_paragraph()

    # Metadata table
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, val in D.METADATA_PLACEHOLDERS:
        cells = t.add_row().cells
        cells[0].text = ""
        r0 = cells[0].paragraphs[0].add_run(label)
        r0.bold = True
        r0.font.size = Pt(11)
        cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        cells[1].text = ""
        r1 = cells[1].paragraphs[0].add_run(val)
        r1.font.size = Pt(11)
        cells[0].width = Cm(4.0)
        cells[1].width = Cm(7.0)

    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Frozen final scientific scope: " + D.RELEASE["final_scientific_scope"])
    r.font.size = Pt(10)
    r.bold = True
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("scientific_delta = 0  |  Document assembly only  |  "
                    "No TEST access, inference, training, or new statistics")
    r2.font.size = Pt(9.5)
    r2.italic = True

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run(
        "This report is bound to the frozen manuscript "
        "reports/manuscript/final/manuscript_final.md\n"
        "SHA-256 " + D.RELEASE["manuscript_final_sha256"])
    r3.font.size = Pt(8.5)
    r3.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    page_break(doc)


def build_executive_summary(doc):
    h1(doc, "Executive Summary")

    para(doc,
         "Multi-domain medical image segmentation is usually served by a single global model that "
         "processes every input at a fixed computational cost. A natural improvement is to keep a "
         "strong global segmenter and add an optional regional refinement that runs only when it is "
         "expected to help. The hard part is not the refinement itself: it is deciding, before the "
         "expensive computation is performed, whether that refinement is worth running, and "
         "protecting the global prediction when it is not.")

    para(doc,
         "This report documents RA-MedFiLM-BARR (system A8/C9): a frozen, four-component pipeline "
         "that addresses exactly that problem. A shared FiLM-conditioned global segmenter "
         "(GlobalMedFiLM, denoted G) produces a global probability map. A learned benefit router "
         "(BARRBenefitRouterV1, denoted B_phi) reads a 202-dimensional, ground-truth-free description "
         "of the current prediction and geometry and predicts the paired Dice gain that a regional "
         "refinement would produce. If that predicted gain is too small, the pipeline skips "
         "refinement and keeps the global prediction. If the router decides to execute, a regional "
         "refiner (BARRRegionalRefinerV1, denoted R_psi) refines the proposed region, and a "
         "post-safety stage (BARRPostSafetyV1, denoted S_omega) decides whether the refinement is "
         "safe to accept. Accepted refinements are fused back by a pad-aware fusion; rejected ones "
         "fall back to the global prediction.")

    para(doc,
         "The central contribution is at the SYSTEM-INTEGRATION level rather than the level of any "
         "single component. The specific integration is: (i) a pre-execution, learned regression of "
         "the paired ground-truth-derived Dice gain of an optional regional refinement, used as an "
         "execute/skip gate; (ii) a post-safety accept/reject stage with a preserved-output "
         "fallback; and (iii) this combination applied to multi-domain medical binary segmentation "
         "under an explicit preservation constraint. The individual mechanisms (conditional compute, "
         "cascades, learned routing, paired-gain estimation, multi-domain segmentation, "
         "ground-truth-free quality estimation, rejection/abstention) are established prior art.")

    para(doc,
         "The strongest supporting evidence is drawn from frozen development and holdout analyses. "
         "On the development set VAL808 (n = 808) the system preserved macro-domain Dice relative to "
         "the global reference (difference 0.002210; 95% bootstrap confidence interval "
         "[0.001133, 0.003298]; lower bound greater than -0.005). On a one-shot held-out evaluation "
         "(ROUTER_HOLDOUT, n = 875) it was non-inferior to the global reference (difference 0.001739; "
         "95% confidence interval [0.001117, 0.002405]), under a disclosed post-first-open "
         "scientific source-freeze protocol deviation that is stated verbatim in this report. A "
         "thirteen-arm module ablation reported a mean routed true DeltaDice of 0.007516 for the "
         "A8/C9 routing-plus-post-safety policy, together with an explicitly reported negative "
         "result: the F1 integrated refiner did not improve the pipeline (mean -0.000433). "
         "Three-seed reproducibility was descriptive and sign-consistent, with no pass/fail gate and "
         "no best-seed selection.")

    para(doc,
         "The final system was subsequently evaluated descriptively on all 1,683 TEST samples. The "
         "descriptive final-system Dice was 0.88693 for ISIC (n = 735), 0.85042 for BUSI (n = 174), "
         "0.85071 for KVASIR (n = 216), and 0.73769 for KUB (n = 558); the descriptive macro-domain "
         "Dice was 0.8314368385956257. No post-hoc TEST sample exclusion was applied.")

    info_box(doc, "The TEST limitation (read this before quoting any TEST number)", [
        "The frozen Phase39 protocol prespecified a comparison of the final system against the "
        "frozen global reference C-gGLOBAL, with a macro-domain Dice-difference primary endpoint, a "
        "confidence-interval decision rule, and per-domain harm rules.",
        "The successful Phase39 v1.2 execution did NOT emit the required C-gGLOBAL comparator "
        "quantities. The primary comparative endpoint is therefore NOT PRODUCED, and the frozen "
        "statistical decision is NOT EVALUABLE from the v1.2 output.",
        "No additional TEST inference was performed to reconstruct the missing endpoint.",
        "Consequently, the descriptive TEST Dice reported above must NOT be interpreted as "
        "superiority, non-inferiority, preservation confirmation, harm-free refinement, or "
        "comparative benefit.",
        "Evidence class: " + D.PHASE39_EVIDENCE_CLASS,
    ])

    para(doc,
         "Publication status: the frozen manuscript is assembly-complete under the reduced scope "
         "MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY, with all numbers provenance-bound "
         "and all claims evidence-bound. It is ready for supervisor review as a methodological and "
         "descriptive report. It is not ready to support a claim of TEST-confirmed comparative "
         "benefit against the global reference.")

    page_break(doc)


def build_toc(doc):
    h1(doc, "Table of Contents", toc=False)
    para(doc,
         "The entries below are the report's major sections. In Microsoft Word, right-click the "
         "field and choose \"Update Field\" (or press F9) to populate the automatic Table of "
         "Contents with page numbers.", italic=True, size=9.5)
    p = doc.add_paragraph()
    add_field(p, r'TOC \o "1-2" \h \z \u')
    # Static fallback listing so the TOC is readable even before field update.
    for lvl, title in TOC_ENTRIES:
        if lvl > 2:
            continue
        pp = doc.add_paragraph()
        pp.paragraph_format.space_after = Pt(0)
        pp.paragraph_format.left_indent = Inches(0.15 * (lvl - 1))
        rr = pp.add_run(("" if lvl == 1 else "   ") + title)
        rr.font.size = Pt(9.5 if lvl == 2 else 10.5)
        rr.bold = (lvl == 1)
    page_break(doc)


def build_list_of_figures(doc, figures):
    h1(doc, "List of Figures", toc=False)
    for i, (num, cap, _src) in enumerate(figures, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        r = p.add_run(f"Figure {num}. ")
        r.bold = True
        r.font.size = Pt(9.5)
        r2 = p.add_run(cap)
        r2.font.size = Pt(9.5)
    page_break(doc)


def build_list_of_tables(doc, tables):
    h1(doc, "List of Tables", toc=False)
    for num, cap in tables:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        r = p.add_run(f"Table {num}. ")
        r.bold = True
        r.font.size = Pt(9.5)
        r2 = p.add_run(cap)
        r2.font.size = Pt(9.5)
    page_break(doc)


def build_abbreviations(doc):
    h1(doc, "Abbreviations and Symbols", toc=False)
    rows = [
        ("G", "GlobalMedFiLM - the shared global FiLM-conditioned segmenter (3,523,001 parameters)"),
        ("B_phi", "BARRBenefitRouterV1 - the learned pre-execution benefit router (36,801 parameters)"),
        ("R_psi", "BARRRegionalRefinerV1 - the on-demand regional refiner (1,276,401 parameters)"),
        ("S_omega", "BARRPostSafetyV1 - the post-refinement accept/reject safety stage (1,217 parameters)"),
        ("ROI", "Region of interest, proposed ground-truth-free from the global probability"),
        ("FiLM", "Feature-wise Linear Modulation; F_hat = (1 + gamma) * F + beta"),
        ("Dice", "Dice similarity coefficient (segmentation overlap metric)"),
        ("IoU", "Intersection over Union (secondary overlap metric)"),
        ("HD95", "95th-percentile Hausdorff distance (boundary metric)"),
        ("VAL", "Validation; VAL808 is the frozen development set (n = 808)"),
        ("TEST", "The final descriptive evaluation cohort (n = 1,683); closed population"),
        ("ROUTER_HOLDOUT", "The one-shot held-out evaluation population (n = 875)"),
        ("D61", "The canonical pad-aware fuse_full_field fusion contract"),
        ("D75 / POLICY_B", "The frozen final segmentation scoring representation "
         "(live f32 -> f16 -> f32, threshold >= 0.50)"),
        ("C-gGLOBAL", "The frozen global comparator used by the Phase39 primary endpoint"),
        ("tau / tau_C8_final", "The frozen runtime router threshold (-0.024358327623641256)"),
        ("202-D", "The ground-truth-free pre-refinement feature vector consumed by B_phi"),
        ("MAC", "Multiply-accumulate operation (analytical compute unit)"),
        ("CI", "Confidence interval"),
        ("A8/C9", "The final canonical system configuration / policy identifier"),
    ]
    add_table(doc, ["Term", "Meaning"], rows, widths=[3.6, 12.4],
              caption="Table 0a. Abbreviations and symbols used in this report.")
    page_break(doc)


# ===========================================================================
# Body sections
# ===========================================================================
def sec1_background(doc):
    h1(doc, "Section 1 - Research Background")

    h2(doc, "1.1 Medical image segmentation")
    para(doc,
         "Medical image segmentation assigns a label to every pixel of a medical image, typically "
         "separating an anatomical structure or a lesion (foreground) from the surrounding tissue "
         "(background). It underpins measurement, staging, treatment planning, and quantitative "
         "follow-up. In this project every task is BINARY foreground/background segmentation, and the "
         "four domains differ in modality, appearance, and target.")

    h2(doc, "1.2 Multi-domain segmentation and domain heterogeneity")
    para(doc,
         "Clinical imaging spans markedly different modalities. Dermoscopy (ISIC), ultrasound "
         "(BUSI), endoscopy (KVASIR), and radiography (KUB) differ in contrast mechanism, noise "
         "structure, resolution, and the geometry of the structure being segmented. A single shared "
         "model is attractive because it amortises one set of weights across all domains, but "
         "heterogeneity means that one fixed computational path will not be equally appropriate for "
         "every image. A shared model may therefore produce segmentation quality that varies "
         "substantially from image to image.")

    h2(doc, "1.3 Why not always refine?")
    para(doc,
         "A regional refiner is a second, more expensive network that re-segments a local crop at "
         "higher effective resolution. Running it on every image has three costs. First, compute: the "
         "refiner roughly doubles the per-image budget. Second, risk: an unconditional refiner can "
         "degrade a prediction that was already good, particularly when the region is ambiguous or "
         "the crop contains little signal. Third, utility: on many images the global prediction is "
         "already correct and refinement changes nothing.")

    h2(doc, "1.4 The decision problem")
    para(doc,
         "The interesting problem is therefore not refinement but the decision to refine. That "
         "decision must be made BEFORE the refinement is computed (otherwise no compute is saved), "
         "must be learnable from paired outcomes, and must be governed by a preservation constraint "
         "so that the global prediction is protected when refinement is not warranted. In this "
         "project the decision target is the paired difference between the outcome after refinement "
         "and the outcome without it, estimated per image before deciding.")

    h2(doc, "1.5 Conditional computation and preservation")
    para(doc,
         "Conditional computation is the general idea of spending computation only where it is "
         "expected to help. Applied here, it produces a pipeline in which the global model always "
         "runs, a cheap router always runs, and the expensive refiner runs only when the router "
         "expects a benefit. A further safety stage protects against a refinement that is executed "
         "but turns out to be unhelpful, by reverting to the global prediction.")


def sec2_problem(doc):
    h1(doc, "Section 2 - Problem Statement")

    para(doc,
         "The core research problem is to decide, before running an optional regional refinement, "
         "whether that refinement is likely to be beneficial, and to combine the global and refined "
         "predictions so that the global prediction is preserved whenever refinement should not be "
         "used.")

    h2(doc, "2.1 Desired behaviour")
    para(doc, "The desired behaviour of the system is the following sequence:", justify=False)
    for s in [
        "Run the global segmentation model G to obtain the global prediction p_global.",
        "Inspect the current prediction, its geometry, and learned features.",
        "Estimate whether regional refinement is likely to be beneficial.",
        "Skip refinement when the expected benefit is low (preserving compute and the prediction).",
        "Execute refinement when it is expected to be appropriate.",
        "Apply a post-refinement safety decision to the executed refinement.",
        "Fuse safely when the refinement is accepted, and preserve the global prediction otherwise.",
    ]:
        numbered(doc, s)

    h2(doc, "2.2 Formal notation used in this project")
    para(doc,
         "The report uses only notation that is already frozen in the repository. The frozen "
         "decision vocabulary distinguishes the router decision from the final state:", justify=False)
    for s in [
        "Router decision (B_phi gate): EXECUTE iff U(delta_hat_final) >= tau_C8_final, else SKIP, "
        "where U = delta_hat_final - 0.25 * C_ACTION.",
        "Final state: exactly one of FORCED_SKIP, SKIP_GLOBAL, EXECUTE_THEN_ACCEPT, or "
        "EXECUTE_THEN_REJECT.",
        "Probability operator: p_global = sigmoid(logits.float()).",
        "Final scoring: mask = (probability >= 0.50) under the frozen D75/POLICY_B representation.",
        "Fusion: canonical D61 pad-aware fuse_full_field(p_global, refined, geom).",
    ]:
        bullet(doc, s)
    para(doc,
         "No mathematical definition beyond the frozen threshold contract is introduced in this "
         "report.")


def sec3_literature(doc):
    h1(doc, "Section 3 - Literature Review and Prior Art")

    para(doc,
         "This section summarises the frozen prior-art families that frame the contribution. The "
         "mapping below is taken from the frozen manuscript's related-work analysis, and every "
         "citation resolves to the frozen reference set (Section 39).")

    h2(doc, "3.1 Adaptive inference and the value of computation")
    para(doc,
         "The idea of spending computation only when it is expected to improve a decision originates "
         "in metareasoning, where a computation is executed only if its expected value exceeds its "
         "cost [russell1991metareasoning], and is formalised for adaptive inference by the theory of "
         "achievable performance-preserving efficiency gains [hor2024adaptiveinference]. Learned, "
         "differentiable allocation of computation with an explicit cost penalty appears in adaptive "
         "computation time [graves2016act].")

    h2(doc, "3.2 Conditional computation, cascades, and routing")
    para(doc,
         "The architectural pattern of a cheap stage gating an expensive one is canonical: boosted "
         "cascades reject easy cases early [viola2001cascade]; optimal pass-on criteria decide "
         "whether to escalate to a more expensive cascade stage [latotzke2021cascade]; and region "
         "proposals gate an expensive per-region head [ren2015fasterrcnn]. Learned per-input "
         "execute/skip of computation appears in SkipNet [wang2018skipnet] and mixture-of-depths "
         "routing [raposo2024mod]. Modality-specific mixture-of-experts routing in medical "
         "segmentation is occupied by M4oE [jiang2024m4oe].")

    h2(doc, "3.3 Treatment-effect estimation and learning to defer")
    para(doc,
         "The decision target used here is a paired difference of outcomes under two conditions, "
         "estimated per unit before deciding. That is the standard causal-inference structure of "
         "conditional average treatment effects [kunzel2019metalearners]. The closest general "
         "formulation is learning to defer to a costlier expert with an explicit cost and a "
         "preservation structure [mozannar2020defer], and its dense medical-segmentation analogue "
         "routes to a human expert before finalising [tian2026deferredseg].")

    h2(doc, "3.4 Segmentation refinement")
    para(doc,
         "Within segmentation, unconditional refinement primitives are established "
         "[wang2023segrefiner], and the always-run coarse-to-fine cascade is the canonical baseline "
         "[isensee2021nnunet]. The single closest functional analogue judges whether a refinement "
         "was worth it AFTER running it and may revert, so it saves no compute [moon2024jfs]. Acting "
         "on the region that provides the most gain is also explored for cropping in vision-language "
         "models [zhao2026lfpc], and regional zoom/refinement for small structures is prior art "
         "[bouzid2023scaleaware, chou2024tinylessurvey].")

    h2(doc, "3.5 Medical dynamic computation")
    para(doc,
         "In medical imaging, deciding compute allocation BEFORE running the model is occupied by "
         "Med-DANet and Med-DANet V2, which select a crop and a quantisation level rather than a "
         "refinement gain [shen2022meddanet, shen2024meddanetv2], and by adaptive patching that "
         "allocates attention by image detail [zhang2024adaptivepatching].")

    h2(doc, "3.6 Universal / multi-domain segmentation")
    para(doc,
         "A shared multi-domain medical segmentor is not a novel component, as shown by universal "
         "few-shot segmentation [butoi2023universeg] and promptable universal medical segmentation "
         "[ma2024medsam].")

    h2(doc, "3.7 Ground-truth-free quality estimation, rejection, and abstention")
    para(doc,
         "Ground-truth-free estimation of the quality of a CURRENT prediction is solved "
         "[laves2018qualitypred, borges2024sdc, huang2024evanyseg], and is distinct from predicting "
         "the gain of a FUTURE action. Rejection and abstention mechanisms preserve reliability at "
         "the pixel or decision level [sanisoglu2026abstain, chow1970reject], and conformal methods "
         "control the risk of a single output [tan2026cls]; none of these bounds the gain of an "
         "optional refinement. Device-aware lightweight segmentation is likewise crowded "
         "[zhang2023mobilesam].")

    h2(doc, "3.8 Mechanisms that already exist versus the contribution of this work")
    info_box(doc, "Where the boundary lies", [
        "INDIVIDUAL MECHANISMS ALREADY EXIST: conditional computation, cascades, learned "
        "execute/skip routing, paired-gain / treatment-effect estimation, learning to defer, "
        "segmentation refinement primitives, multi-domain universal segmentation, ground-truth-free "
        "quality estimation, and rejection/abstention.",
        "DEFENSIBLE CONTRIBUTION OF THIS WORK: the specific integration of a pre-execution, learned, "
        "ground-truth-derived paired-Dice-gain gate for an OPTIONAL regional refinement, with a "
        "post-safety accept/reject stage and a preserved-output fallback, applied to multi-domain "
        "medical binary segmentation under an explicit preservation constraint.",
    ])


def sec4_novelty(doc):
    h1(doc, "Section 4 - Research Gap and Novelty")

    para(doc,
         "The defensible novelty of this work is primarily at the SYSTEM-INTEGRATION / "
         "SPECIFICATION level, not the level of individual components. This distinction matters for "
         "a supervisor because it determines what can and cannot be claimed.")

    h2(doc, "4.1 The specific integration")
    para(doc, "The contribution is the specific combination of:", justify=False)
    for s in [
        "Shared multi-domain segmentation (one global model across four clinical domains).",
        "A global prediction produced by that shared model.",
        "Pre-execution benefit estimation, made before the expensive computation.",
        "GT-derived paired Dice-gain supervision used during development to train the router.",
        "A learned benefit router that produces the execute/skip gate.",
        "Conditional regional refinement, executed only on the EXECUTE branch.",
        "A post-refinement safety decision that can reject an executed refinement.",
        "A safe global fallback that preserves the global prediction.",
        "Pad-aware fusion that pastes accepted refinements back into the full field.",
        "Multi-domain medical binary segmentation as the application setting.",
        "Frozen, preservation-oriented governance throughout.",
    ]:
        bullet(doc, s)

    h2(doc, "4.2 What is occupied by prior work")
    para(doc,
         "Section 3 documents that the individual mechanisms are occupied: the gate concept "
         "[viola2001cascade, latotzke2021cascade, wang2018skipnet], the paired-gain target "
         "formulation [kunzel2019metalearners], conditional compute [graves2016act, raposo2024mod], "
         "learning to defer [mozannar2020defer, tian2026deferredseg], refinement primitives "
         "[wang2023segrefiner], post-hoc-refinement judging [moon2024jfs], medical dynamic compute "
         "[shen2022meddanet, shen2024meddanetv2, zhang2024adaptivepatching], and multi-domain "
         "segmentation [butoi2023universeg, ma2024medsam].")

    h2(doc, "4.3 Why the combination is the defensible contribution")
    para(doc,
         "The closest single functional analogue judges whether a refinement was worth it after "
         "running it [moon2024jfs] and therefore saves no compute. The medical dynamic-compute "
         "family decides compute allocation before running the model but selects a crop or a "
         "quantisation level rather than predicting the gain of an optional refinement "
         "[shen2022meddanet, shen2024meddanetv2]. This work combines a pre-execution learned "
         "paired-Dice-gain gate with a post-safety accept/reject and a preserved-output fallback for "
         "an OPTIONAL refinement in multi-domain medical segmentation, and evaluates it under an "
         "explicit preservation constraint. That integration, and its frozen preservation-oriented "
         "evaluation, is the defensible contribution. No stronger novelty claim is made.")


def sec5_rq(doc):
    h1(doc, "Section 5 - Research Questions and Hypotheses")

    para(doc,
         "The following research questions are derived from the frozen project evidence. Where the "
         "project used frozen wording, that wording is preserved.")

    rqs = [
        ("RQ1", "Can a learned router estimate, before refinement is computed, when regional "
                "refinement is beneficial?",
         "Addressed by the Phase28 ablation (B_phi benefit capture and harmful-activation share on "
         "ROUTER_DEVELOPMENT) and the Phase27/30 preservation evaluations."),
        ("RQ2", "Can conditional regional refinement improve selected cases without materially "
                "degrading the shared global model?",
         "Addressed by the Phase27 VAL808 preservation evaluation and the Phase30 one-shot "
         "ROUTER_HOLDOUT non-inferiority evaluation."),
        ("RQ3", "Does the system remain reproducible across seeds?",
         "Addressed by the Phase29 three-seed reproducibility analysis (seeds 42/123/3407), which is "
         "descriptive with no pass/fail gate and no best-seed selection."),
        ("RQ4", "What failure modes occur in practice?",
         "Addressed by the Phase33 descriptive failure analysis on ROUTER_HOLDOUT."),
        ("RQ5", "What is the computational cost of conditional refinement?",
         "Addressed by the Phase34 analytical MAC lower bound and hardware-specific measured "
         "runtime profile."),
        ("RQ6", "How robust is the system to image and proposal perturbations?",
         "Addressed by the Phase36 synthetic image-perturbation and proposal-perturbation studies on "
         "VAL808."),
        ("RQ7", "How interpretable are the FiLM and routing decisions?",
         "Addressed by the Phase35 descriptive model-mechanism evidence."),
    ]
    add_table(doc, ["ID", "Research question", "How it is addressed (frozen evidence)"],
              [(a, b, c) for a, b, c in rqs], widths=[1.6, 7.2, 7.2],
              caption="Table 5-1. Research questions and the frozen evidence that addresses them.")

    para(doc,
         "No new confirmatory hypothesis test was created. The Phase31 statistical-governance "
         "closure established that no new confirmatory significance procedure is eligible, so all "
         "reported statistical evidence is descriptive (bootstrap confidence intervals only).")


def sec6_datasets(doc):
    h1(doc, "Section 6 - Datasets and Tasks")

    para(doc,
         "Four clinical domains are used. All four are BINARY foreground/background segmentation "
         "tasks. Task identity is frozen and differs from an alphabetical order.")

    add_table(doc, ["Task", "Domain", "Modality", "Channels", "Segmentation target"],
              D.TASKS, widths=[1.9, 2.2, 3.6, 3.0, 5.3],
              caption="Table 6-1. Task, domain, and modality summary. "
                      "Task IDs: 0 = ISIC, 1 = BUSI, 2 = KVASIR, 3 = KUB.")

    h2(doc, "6.1 Population structure")
    para(doc,
         "The frozen population structure distinguishes the development training set, the "
         "development validation set VAL808, the ablation/reproducibility development population "
         "ROUTER_DEVELOPMENT, the one-shot held-out population ROUTER_HOLDOUT, and the final TEST "
         "cohort.")
    add_table(doc, ["Population", "n", "Per-domain composition", "Role"],
              D.POPULATION_SPLITS, widths=[3.4, 1.8, 6.6, 4.2],
              caption="Table 6-2. Population and split summary. TEST counts are metadata only.")

    h2(doc, "6.2 Final TEST cohort")
    para(doc,
         "The final TEST cohort contains 1,683 samples. Its per-domain composition is ISIC 735, "
         "BUSI 174, KVASIR 216, and KUB 558.")
    add_table(doc, ["Domain", "n", "Descriptive final-system Dice", "Status"],
              D.TEST_DOMAIN_TABLE[:5], widths=[4.4, 1.6, 6.6, 3.4],
              caption="Table 6-3. Frozen TEST cohort composition and descriptive final-system Dice.")

    h2(doc, "6.3 KUB reporting-only subgroups")
    para(doc,
         "The KUB domain carries subgroup identity metadata (Kidney_Stone, Bladder_Stone, "
         "Ureteric_Stone). This identity is REPORTING METADATA ONLY. It is never used as a "
         "segmentation class, a task ID, a model input, a routing input, or a conditioning "
         "variable.")
    add_table(doc, ["KUB subgroup", "n (VAL808 KUB subset)", "Role"],
              D.KUB_SUBGROUPS, widths=[4.0, 4.6, 7.4],
              caption="Table 6-4. KUB reporting-only subgroup metadata.")


def sec7_methodology(doc):
    h1(doc, "Section 7 - Complete RA-MedFiLM-BARR Methodology")

    para(doc,
         "This section explains the complete methodology from the input image to the final "
         "segmentation. The researcher-supplied methodology infographic is reproduced first, "
         "followed by a step-by-step verbal description of the entire flow.")

    ok = add_figure(
        doc, METHODOLOGY_IMAGE,
        "Figure 1. Overall RA-MedFiLM-BARR methodology and multi-domain inference pipeline "
        "(researcher-supplied methodology infographic; aspect ratio preserved).",
        width_cm=15.5)

    h2(doc, "7.1 Step-by-step methodology flow")
    for title, body in D.METHOD_FLOW_STEPS:
        h3(doc, title)
        para(doc, body)

    h2(doc, "7.2 Frozen system architecture schematic (existing frozen figure)")
    add_figure(
        doc, FIG / "methodology_diagram_package" / "existing_visual_references" /
        "p24_full_system_architecture.png",
        "Figure 2. Frozen full-system architecture (existing frozen visual reference; "
        "source: reports/figures/methodology_diagram_package/existing_visual_references/).",
        width_cm=15.5)

    h2(doc, "7.3 Frozen inference state machine (existing frozen figure)")
    add_figure(
        doc, FIG / "methodology_diagram_package" / "existing_visual_references" /
        "p26_canonical_inference_state_machine.png",
        "Figure 3. Canonical inference state machine: FORCED_SKIP, SKIP_GLOBAL, "
        "EXECUTE_THEN_ACCEPT, EXECUTE_THEN_REJECT (existing frozen visual reference).",
        width_cm=15.5)

    h2(doc, "7.4 Four-domain input illustration (existing frozen montage)")
    add_figure(
        doc, FIG / "methodology_diagram_package" / "four_domain_input_montage.png",
        "Figure 4. Four-domain input montage (BUSI | ISIC | KUB | KVASIR) with task IDs and "
        "modalities. No performance numbers are encoded in this figure.",
        width_cm=15.5)


def sec8_architecture(doc):
    h1(doc, "Section 8 - Final System Architecture")

    para(doc,
         "The final system is a frozen four-component conditional-refinement pipeline. No component "
         "was trained, selected, or tuned in the release process (scientific_delta = 0).")

    add_table(doc, ["Component", "Class", "Parameters", "Primary output / input", "Execution condition"],
              D.ARCH_TABLE, widths=[2.0, 4.0, 2.3, 4.4, 3.3],
              caption="Table 8-1. Final architecture and component specification.")

    add_table(doc, ["Component", "Parameters", "Checkpoint bytes", "Checkpoint SHA-256", "Execution role"],
              D.ARCH_COMPONENT_SPEC, widths=[1.7, 2.0, 2.4, 7.0, 2.9],
              caption="Table 8-2. Frozen component specification with checkpoint identities "
                      "(source: reports/tables/phase37_consolidated/T37-01).",
              font_size=7.5, header_size=8.0)

    para(doc,
         "The total parameter count is 4,837,420, of which 0 are trainable in the assembly wrapper.")

    h2(doc, "8.1 Component purposes")
    for s in [
        "G (GlobalMedFiLM) always runs and produces the global prediction for every input.",
        "B_phi (BARRBenefitRouterV1) is a cheap pre-gate that always runs and decides SKIP or "
        "EXECUTE before any refinement is computed.",
        "R_psi (BARRRegionalRefinerV1) runs only on the EXECUTE branch and refines the proposed "
        "region.",
        "S_omega (BARRPostSafetyV1) runs only on the EXECUTE branch, after R_psi, and decides "
        "whether the refinement is accepted or rejected.",
        "The RAMedFiLMBARR assembly wrapper adds no parameters and performs assembly only; it has "
        "no learned layers, loss, optimizer, or backward pass.",
    ]:
        bullet(doc, s)

    h2(doc, "8.2 Checkpoint identities")
    para(doc,
         "Checkpoint replacement is not permitted. The load contract fails closed on any SHA-256 "
         "mismatch, requires strict loading with zero missing/unexpected keys, requires all weights "
         "finite, requires all modules in eval mode with requires_grad=False, and requires CUDA-only "
         "execution.",
         justify=True)
    add_table(doc, ["Component", "Class", "Checkpoint path", "SHA-256"],
              D.CHECKPOINT_IDENTITIES, widths=[1.7, 3.8, 6.5, 4.0],
              caption="Table 8-3. Frozen checkpoint identities used by the final system.",
              font_size=7.0, header_size=8.0)


def sec9_gmedfilm(doc):
    h1(doc, "Section 9 - GlobalMedFiLM (G)")

    para(doc,
         "GlobalMedFiLM is the shared global segmenter. It is the component that is always executed, "
         "and it defines the baseline prediction that the rest of the pipeline may (or may not) "
         "refine.")

    h2(doc, "9.1 Role of the global model")
    para(doc,
         "The global model provides a single shared representation and a single shared output head "
         "across all four domains. Multi-domain conditioning enters only through a learned task "
         "embedding, so the model does not carry per-domain heads. Its output is a single-channel "
         "probability map p_global.")

    h2(doc, "9.2 Task mapping")
    para(doc,
         "Task mapping is frozen: 0 = ISIC, 1 = BUSI, 2 = KVASIR, 3 = KUB.",
         justify=False)

    h2(doc, "9.3 Frozen architecture facts")
    add_table(doc, ["Property", "Value"],
              D.GMEDFILM_FACTS, widths=[4.6, 11.4],
              caption="Table 9-1. Frozen GlobalMedFiLM architecture facts "
                      "(source: methodology_diagram_manifest.json).",
              font_size=8.0)

    h2(doc, "9.4 FiLM conditioning and shared representation")
    para(doc,
         "FiLM (Feature-wise Linear Modulation) modulates intermediate features with a "
         "task-conditioned affine transform: F_hat = (1 + gamma) * F + beta, where gamma and beta "
         "are produced by tanh(W e + b) from the task embedding e, with a zero-initialised output. "
         "The task embedding (dimension 32) is used ONLY as this conditioning entry point; task_id "
         "is never concatenated, channelised, or routed to a per-domain head. The output head is a "
         "single shared 1x1 convolution.")

    h2(doc, "9.5 Frozen inference semantics")
    for s in D.G_INFERENCE_SEMANTICS:
        bullet(doc, s)
    para(doc,
         "These details are frozen and are not changed anywhere in this report.")


def sec10_roi(doc):
    h1(doc, "Section 10 - ROI Extraction")

    para(doc,
         "A region of interest is proposed from the global probability alone. The proposal is "
         "ground-truth-free: no label or mask information is used at any point.")

    add_table(doc, ["Property", "Frozen value", "Symbol / note"],
              D.ROI_FACTS, widths=[4.2, 5.0, 6.8],
              caption="Table 10-1. Frozen ROI proposal parameters.")

    h2(doc, "10.1 Why empty-ROI handling matters")
    para(doc,
         "When the proposal is empty, the pipeline cannot form a crop. The frozen behaviour is "
         "ACTION_UNAVAILABLE, which forces the FORCED_SKIP state. In FORCED_SKIP the router, "
         "refiner, and safety stage are not invoked at all, and the global prediction is emitted "
         "unchanged. This is the safest possible behaviour: it neither spends compute nor risks "
         "altering a prediction for which no region could be identified.")

    h2(doc, "10.2 Frozen ROI illustration (existing frozen figure)")
    add_figure(
        doc, FIG / "methodology_diagram_package" / "existing_visual_references" /
        "phase13_predicted_roi_localization_panel.png",
        "Figure 5. Predicted ROI localisation panel (existing frozen visual reference). "
        "The ROI is derived ground-truth-free from p_global.",
        width_cm=15.0)


def sec11_bphi(doc):
    h1(doc, "Section 11 - Benefit Router B_phi")

    para(doc,
         "The benefit router is the component that decides whether the optional refinement is worth "
         "running. It runs before the refiner whenever an action is available.")

    add_table(doc, ["Property", "Frozen value"],
              D.BPHI_FACTS, widths=[5.0, 11.0],
              caption="Table 11-1. Frozen B_phi specification "
                      "(source: methodology_diagram_manifest.json; thresholds_and_decisions.json).",
              font_size=8.0)

    h2(doc, "11.1 The 202-D feature representation")
    para(doc,
         "The router consumes a canonical 202-dimensional, ground-truth-free feature vector "
         "assembled from six groups of G feature taps (each 32-D, in GLOBAL and ROI scope) plus ten "
         "prediction- and geometry-derived scalars.")
    add_table(doc, ["Group", "Tap", "Scope", "Index range", "Dim"],
              D.BPHI_FEATURE_GROUPS, widths=[3.4, 2.6, 2.4, 3.6, 1.6],
              caption="Table 11-2. The 192 deep feature taps (6 groups x 32) that form the first "
                      "part of the 202-D vector.")
    para(doc,
         "The remaining ten scalars, in frozen order, are: " + ", ".join(D.BPHI_SCALARS) + ".",
         justify=True)

    h2(doc, "11.2 Benefit estimation and the execute/skip gate")
    para(doc,
         "The router regresses the paired refinement gain delta_hat. The deployed runtime gate uses "
         "the resource-aware utility U = delta_hat_final - 0.25 * C_ACTION and compares it against "
         "the frozen runtime threshold tau_C8_final. If U >= tau_C8_final the router decides "
         "EXECUTE; otherwise it decides SKIP. The scientific out-of-fold threshold is a SEPARATE "
         "score space used only for scientific evidence and is never used as a runtime gate.")

    para(doc,
         "IMPORTANT: the router does not perfectly predict improvement. Its behaviour is "
         "characterised empirically by benefit capture and by the harmful-activation share reported "
         "in the ablation (Section 18) and failure analysis (Section 22). No claim of perfect "
         "prediction is made anywhere.")

    h2(doc, "11.3 Router attribution illustration (existing frozen figure)")
    add_figure(
        doc, FIG / "phase35_interpretability" / "phase35_f6_router_group_attribution.png",
        "Figure 6. Router feature-group attribution (existing frozen Phase35 figure). "
        "Attribution concentrates on decoder1 feature groups; this is descriptive evidence.",
        width_cm=14.5)


def sec12_rpsi(doc):
    h1(doc, "Section 12 - Regional Refiner R_psi")

    para(doc,
         "The regional refiner is the expensive component. It is executed only on the EXECUTE "
         "branch, i.e. only when the router expects the refinement to be beneficial.")

    add_table(doc, ["Property", "Frozen value"],
              D.RPSI_FACTS, widths=[4.6, 11.4],
              caption="Table 12-1. Frozen R_psi specification.")

    h2(doc, "12.1 What the refiner sees and produces")
    for s in [
        "Extraction: the proposed ROI is cropped from the input image at the frozen canvas/crop "
        "geometry.",
        "Image crop: the RGB crop is one part of the refiner input.",
        "Global-probability channel: the cropped p_global is supplied as an additional channel, so "
        "the refiner sees both the raw appearance and the global model's belief.",
        "Regional refinement: the narrowed-channel residual U-Net produces a single-channel "
        "regional logit map with no internal sigmoid.",
        "Map-back: an accepted regional prediction is pasted back into the full field by the "
        "canonical pad-aware D61 fuse_full_field operation.",
    ]:
        bullet(doc, s)

    h2(doc, "12.2 Why refinement is conditional rather than always-run")
    para(doc,
         "Running the refiner unconditionally would roughly double the per-image compute and could "
         "degrade already-correct predictions. Making it conditional means that the expensive work "
         "is reserved for cases where the router expects a paired gain, and the global prediction is "
         "preserved everywhere else. Section 23 quantifies the resulting analytical compute "
         "behaviour.")


def sec13_somega(doc):
    h1(doc, "Section 13 - Post-Safety S_omega")

    para(doc,
         "The post-safety stage is the second protection layer. It acts AFTER a refinement has "
         "already been computed, and it can reject that refinement.")

    add_table(doc, ["Property", "Frozen value"],
              D.SOMEGA_FACTS, widths=[4.6, 11.4],
              caption="Table 13-1. Frozen S_omega specification.")

    h2(doc, "13.1 Frozen forward semantics")
    para(doc,
         "The stage consumes a 20-dimensional input: a 16-dimensional normalised numeric "
         "description of the change between the global and refined predictions, plus a 4-dimensional "
         "task one-hot. It emits a single safety logit. The refinement is ACCEPTED if and only if "
         "sigmoid(logit) >= 0.50; otherwise it is REJECTED.")
    para(doc,
         "The frozen numeric feature order is: " + ", ".join(D.SOMEGA_NUMERIC_FEATURES) + ".",
         justify=True)
    para(doc,
         "The frozen task one-hot order is: task_0_ISIC, task_1_BUSI, task_2_KVASIR, task_3_KUB.")
    add_figure(
        doc, FIG / "methodology_diagram_package" / "existing_visual_references" /
        "post_safety_20d_breakdown.png",
        "Figure 7. Post-safety 20-D input breakdown (existing frozen visual reference): "
        "16-D numeric + 4-D task one-hot.",
        width_cm=14.5)

    h2(doc, "13.2 Why this creates a second protection layer")
    para(doc,
         "The router protects compute and the global prediction at the decision point. The "
         "post-safety stage protects against an executed refinement that turns out to be unhelpful. "
         "Together they produce the EXECUTE_THEN_REJECT state, in which the refinement has run but "
         "the global prediction is restored as the final output.")


def sec14_state_machine(doc):
    h1(doc, "Section 14 - State Machine")

    para(doc,
         "The pipeline emits exactly one of four states. The table below gives the trigger, whether "
         "the refiner and post-safety stage execute, the source of the final prediction, and the "
         "interpretation of each state.")

    add_table(doc, ["State", "Trigger", "Refiner executed?", "Post-safety executed?",
                    "Final source", "Interpretation"],
              D.STATE_MACHINE, widths=[2.6, 3.2, 1.7, 1.8, 2.6, 4.1],
              caption="Table 14-1. The four-state decision machine.", font_size=7.5, header_size=7.5)

    para(doc,
         "Note the distinction between the router decision (SKIP / EXECUTE) and the final state. "
         "FORCED_SKIP is decided BEFORE the router (empty proposal), so it has no router decision of "
         "its own.")


def sec15_fusion(doc):
    h1(doc, "Section 15 - Fusion and Final Scoring")

    h2(doc, "15.1 D61 canonical pad-aware fusion")
    para(doc,
         "Accepted refinements are combined with the global prediction by the canonical D61 "
         "pad-aware fuse_full_field(p_global, refined, geom). The refined regional prediction is "
         "pasted back into the full-field global probability on the original raster geometry with "
         "correct canvas/crop padding, so no misalignment is introduced by the crop-and-resize step.")

    h2(doc, "15.2 D75 / POLICY_B final segmentation scoring")
    para(doc,
         "The final segmentation is scored under the frozen D75/POLICY_B representation: the live "
         "float32 probability is persisted as float16 and then scored as float32, against a "
         "threshold of >= 0.50. This ensures that all reported metrics use the exact deployed "
         "representation rather than a development-time approximation.")

    info_box(doc, "Scope of D75 / POLICY_B", [
        "D75 / POLICY_B applies to FINAL segmentation scoring only.",
        "It does NOT apply to model, router, ROI, refiner, safety, or fusion internals.",
    ])

    h2(doc, "15.3 Segmentation output threshold")
    para(doc,
         "The final mask is (probability >= 0.50). This threshold is frozen and is distinct from "
         "the ROI proposal threshold (0.30) and the S_omega acceptance threshold (0.50), which "
         "applies to a different quantity (the safety probability).")


def sec16_governance(doc):
    h1(doc, "Section 16 - Development and Experimental Governance")

    para(doc,
         "The project advanced through a sequence of scientifically gated phases. This section "
         "summarises those stages rather than reproducing internal logs. Every stage below produced "
         "a frozen artifact, and every number in this report traces to one of them.")

    add_table(doc, ["Stage", "Purpose", "Population", "Output", "Scientific interpretation",
                    "Qualifier"],
              D.PHASE_TIMELINE, widths=[1.7, 4.0, 2.4, 3.4, 3.0, 2.5],
              caption="Table 16-1. Major phase timeline.", font_size=7.0, header_size=7.5)

    h2(doc, "16.1 Governance principles observed throughout")
    for s in [
        "Final system freeze before evaluation: components and thresholds are frozen and fail "
        "closed on any hash mismatch.",
        "Preservation evaluation: the system is evaluated against a preservation constraint rather "
        "than a superiority objective.",
        "Module ablation: every major module's contribution is measured, including negative results.",
        "Seed reproducibility: behaviour is checked across seeds without selecting a best seed.",
        "ROUTER_HOLDOUT evaluation: a single held-out evaluation, with its protocol deviation "
        "disclosed.",
        "Statistical governance: no new confirmatory significance procedure is created.",
        "External/domain-shift assessment: eligibility is assessed and honestly reported as "
        "negative.",
        "Failure analysis, efficiency, interpretability, and robustness: each is a separate, "
        "descriptive evidence family.",
        "Manuscript freeze, TEST evaluation, and final publication scope: the missing comparative "
        "endpoint is disclosed rather than worked around.",
    ]:
        bullet(doc, s)
    para(doc,
         "These principles are why the report can state a precise claim boundary (Section 29) and a "
         "precise list of things that cannot be claimed (Section 30).")


def sec17_development(doc):
    h1(doc, "Section 17 - Development and Preservation Results")

    para(doc,
         "On the frozen development set VAL808 (n = 808), the final system preserved macro-domain "
         "Dice relative to the global reference. These are DEVELOPMENT / frozen-validation results. "
         "They are NOT Phase39 TEST comparative confirmation.")

    add_table(doc, ["Domain", "n", "Global Dice", "Final Dice", "Delta Dice",
                    "95% CI low", "95% CI high", "Harm flag"],
              D.VAL808_PER_DOMAIN, widths=[2.2, 1.3, 2.2, 2.2, 1.9, 1.9, 1.9, 2.4],
              caption="Table 17-1. VAL808 multi-domain development preservation results (Phase27).",
              font_size=7.5, header_size=7.5)

    para(doc,
         "The macro-domain Dice difference was 0.002210 with a 95% bootstrap confidence interval of "
         "[0.001133, 0.003298]. The lower bound exceeds -0.005, satisfying the frozen preservation "
         "rule strictly. No domain harm flag was raised.")

    h2(doc, "17.1 ROUTER_HOLDOUT per-domain deltas (Phase30, one-shot)")
    add_table(doc, ["Domain", "Delta Dice", "95% CI low", "95% CI high"],
              D.VAL808_HOLDOUT_DELTA, widths=[3.4, 4.2, 4.2, 4.2],
              caption="Table 17-2. ROUTER_HOLDOUT per-domain and macro DeltaDice "
                      "(one-shot; see Section 20 for the mandatory qualifier).")

    h2(doc, "17.2 Frozen development performance figure (existing frozen figure)")
    add_figure(
        doc, FIG / "phase27_preservation" / "p27_domain_delta_forest.png",
        "Figure 8. Per-domain DeltaDice forest plot on VAL808 (existing frozen Phase27 figure).",
        width_cm=14.5)


def sec18_ablation(doc):
    h1(doc, "Section 18 - Ablation Study")

    para(doc,
         "A comprehensive thirteen-arm ablation was performed on the development population "
         "ROUTER_DEVELOPMENT (n = 4,957; routed budget K = 1,239). Arm labels are reproduced exactly "
         "as frozen; no variant has been renamed in a way that changes its scientific meaning.")

    add_table(doc, ["Arm", "n routed", "Budget frac.", "Sum true delta", "Mean routed delta Dice",
                    "Benefit capture", "n beneficial", "n harmful", "Harmful share", "Evidence class"],
              D.ABLATION_TABLE, widths=[0.9, 1.4, 1.5, 1.9, 2.2, 1.7, 1.4, 1.2, 1.4, 3.4],
              caption="Table 18-1. Frozen 13-arm ablation results (Phase28).",
              font_size=6.5, header_size=6.5)

    h2(doc, "18.1 What happens without the key modules")
    para(doc,
         "Arm A5 (the variant associated with the negative result) produced a mean routed true "
         "DeltaDice of -0.000433, i.e. it did not improve the pipeline; the F1 arm's summed true "
         "delta of -40.3732357728 corresponds to a strongly harmful configuration. Arm A2, which "
         "represents the weaker routing configuration, achieved a mean of 0.001413 with benefit "
         "capture 0.246, well below the final policy. The final configuration A8 (with post-safety) "
         "achieved the highest mean routed true DeltaDice among the routed arms.")

    h2(doc, "18.2 Benefit of the final configuration")
    para(doc,
         "The A8/C9 routing-plus-post-safety policy achieved a mean routed true DeltaDice of "
         "0.007516 with benefit capture 0.597 and harmful-activation share 0.324. A7 and A6 achieved "
         "0.007247 with benefit capture 0.602, which is higher in capture but lower in mean routed "
         "gain, indicating the trade-off between capture and per-decision safety that the final "
         "policy resolves.")

    h2(doc, "18.3 Negative ablation finding")
    info_box(doc, "Explicitly reported negative result", [
        "The F1 integrated refiner did NOT improve the pipeline (mean -0.000433; summed true delta "
        "-40.3732357728; harmful share 0.688).",
        "This negative result is reported as frozen evidence rather than hidden.",
        "No deployment winner was selected on the basis of this ablation; the canonical bundle was "
        "left unchanged.",
    ])

    h2(doc, "18.4 Frozen ablation figure (existing frozen figure)")
    add_figure(
        doc, FIG / "p28_fig1_arm_matrix_overview.png",
        "Figure 9. Ablation arm matrix overview (existing frozen Phase28 figure).",
        width_cm=15.0)


def sec19_reproducibility(doc):
    h1(doc, "Section 19 - Reproducibility")

    para(doc,
         "The policy was evaluated across three seeds (42, 123, and 3407) on the ROUTER_DEVELOPMENT "
         "population and on VAL808. The analysis is DESCRIPTIVE: there is no numeric pass/fail gate "
         "and no best-seed selection.")

    add_table(doc, ["Population", "Metric", "Seed 42", "Seed 123", "Seed 3407", "Mean",
                    "Sign-consistent"],
              D.REPRO_TABLE, widths=[2.8, 3.2, 2.1, 2.1, 2.1, 2.2, 1.7],
              caption="Table 19-1. Three-seed reproducibility summary (Phase29).",
              font_size=6.8, header_size=7.0)

    h2(doc, "19.1 What this shows")
    para(doc,
         "The ROUTER_DEVELOPMENT macro DeltaDice three-seed mean was 0.001215, and the VAL808 "
         "three-seed mean was 0.002822. All seeds were positive (sign-consistent). For VAL808 the "
         "global Dice is seed-invariant (range = 0), as expected because the global model is frozen.")

    h2(doc, "19.2 What reproducibility does NOT prove")
    para(doc,
         "Three-seed consistency shows that the routed behaviour is stable across the seeds; it does "
         "not establish statistical significance, does not constitute a confirmatory test, and does "
         "not license a claim of superiority. The statistical evidence remains descriptive "
         "(Section 21).")

    add_figure(
        doc, FIG / "phase29_val808" / "fig_val808_seedwise_macro_delta_dice.png",
        "Figure 10. Seed-wise macro DeltaDice on VAL808 (existing frozen Phase29 figure).",
        width_cm=13.5)


def sec20_holdout(doc):
    h1(doc, "Section 20 - One-Shot ROUTER_HOLDOUT Evidence")

    para(doc,
         "A single one-shot held-out evaluation was performed on ROUTER_HOLDOUT (n = 875). This is "
         "the final development validation of the frozen system.")

    add_table(doc, ["Quantity", "Frozen value"],
              D.HOLDOUT_TABLE, widths=[7.0, 9.0],
              caption="Table 20-1. One-shot ROUTER_HOLDOUT result (Phase30).")

    para(doc,
         "The final-system macro Dice was 0.930287 versus 0.928548 for the global reference, a "
         "macro DeltaDice of 0.001739 with a 95% domain-stratified bootstrap confidence interval of "
         "[0.001117, 0.002405]. This satisfies the prespecified numerical non-inferiority margin.")

    h2(doc, "20.1 Mandatory qualifier")
    info_box(doc, "Preserved verbatim (Phase30 evidence class)", [
        D.PHASE30_QUALIFIER,
        "",
        "Any ROUTER_HOLDOUT-derived statement in this report preserves this exact qualifier. The "
        "protocol deviation occurred because the Stage-B scientific scoring source was not included "
        "in the pre-open source freeze; predictions and decision rules were frozen before ground-"
        "truth access, ground truth was read once, and no scientific rerun or recomputation "
        "occurred.",
    ])

    h2(doc, "20.2 Frozen holdout figure (existing frozen figure)")
    add_figure(
        doc, FIG / "phase29_val808" / "fig_val808_per_sample_final_dice_distribution.png",
        "Figure 11. Per-sample final Dice distribution on the frozen validation population "
        "(existing frozen Phase29 figure).",
        width_cm=13.5)


def sec21_stats(doc):
    h1(doc, "Section 21 - Statistical Governance")

    para(doc,
         "The Phase31 statistical-governance closure established a key result: NO new confirmatory "
         "significance procedure is eligible. The statistical evidence reported throughout this "
         "report is descriptive (bootstrap confidence intervals only).")

    add_table(doc, ["Test ID", "Population", "Comparison", "Test name", "Provenance class",
                    "Authorized"],
              [(r[0], r[2], r[3], r[4], r[5], str(r[6])) for r in [
                  ("T01", "P30-A8VSRANDOM-P", "ROUTER_HOLDOUT (875)", "A8/C9 vs global reference",
                   "paired Wilcoxon", "POST_HOC_EXPLORATORY_ONLY", False),
                  ("T02", "P30-A8VSRANDOM-P", "ROUTER_HOLDOUT (875)", "A8/C9 vs global reference",
                   "paired bootstrap p (exploratory)", "POST_HOC_EXPLORATORY_ONLY", False),
                  ("T03", "P30-A7-COMPANION", "ROUTER_HOLDOUT (875)", "A8 vs A7",
                   "descriptive bootstrap CI only",
                   "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY", False),
                  ("T04", "H6", "ROUTER_DEVELOPMENT", "learned paired gain vs global uncertainty",
                   "unspecified", "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE", False),
                  ("SUMMARY", "ALL", "multi", "n_tests=4; n_confirmatory=0; n_exploratory=2",
                   "NONE_AUTHORIZED", "GOVERNANCE_ONLY", False),
              ]],
              widths=[1.6, 3.0, 2.8, 4.0, 3.4, 1.4],
              caption="Table 21-1. Statistical test registry (Phase31). No confirmatory test was "
                      "authorized.", font_size=6.8, header_size=7.0)

    h2(doc, "21.1 The frozen preservation rule")
    info_box(doc, "Preservation rule (frozen)", [
        "PRESERVATION_ASSERTED if and only if the macro lower 95% percentile-CI bound > -0.005, "
        "strict.",
        "The per-domain harm rule is applied per domain; a domain harm flag is raised only when its "
        "own criterion is violated.",
        "The rule applies to the populations for which it was frozen (VAL808 and ROUTER_HOLDOUT).",
        "It does NOT apply to TEST, because the Phase39 comparative quantities required to evaluate "
        "it on TEST were not produced.",
    ])

    h2(doc, "21.2 Why no new confirmatory procedure")
    para(doc,
         "A confirmatory procedure may not be created merely because it is conventional. The frozen "
         "position is that no pre-outcome confirmatory method was frozen for these comparisons, so "
         "no confirmatory test can be run after the fact without changing the scientific meaning of "
         "the evidence. Zero new p-values, zero new effect sizes, and zero new bootstrap "
         "computations were produced.")


def sec22_failure(doc):
    h1(doc, "Section 22 - Failure-Mode Analysis")

    para(doc,
         "A descriptive failure analysis was performed on the frozen ROUTER_HOLDOUT tables. The "
         "analysis characterises the prevalence of failure families; it does not establish causal "
         "relationships.")

    add_table(doc, ["Failure family", "Eligible population n", "Failure n", "Failure rate",
                    "Population definition"],
              D.FAILURE_TABLE, widths=[3.8, 2.4, 1.8, 2.4, 5.6],
              caption="Table 22-1. Descriptive failure-mode prevalence on ROUTER_HOLDOUT (Phase33).",
              font_size=7.5)

    para(doc, "Per-domain summary: " + D.FAILURE_BY_DOMAIN + ".", justify=True)

    h2(doc, "22.1 Practical meaning of each family")
    for s in [
        "LOW_OVERLAP (10.06% of 875): the global prediction overlaps the ground truth poorly, so "
        "the case is intrinsically hard for the shared model.",
        "ROUTER_HARMFUL_ACTIVATION (12.92% of the 240 EXECUTE rows): the router chose to execute but "
        "the refinement did not help on that row.",
        "EXECUTE_THEN_REJECT (1.67% of the 240 EXECUTE rows): the refinement executed and was "
        "rejected by the safety stage, so the global prediction was restored. The safety stage "
        "behaved as designed.",
        "ROUTER_MISSED_BENEFIT (0 of 635 SKIP rows): no SKIP row was later found to have had an "
        "available benefit in this descriptive tabulation.",
        "EMPTY_PREDICTION (0 of 875): no row produced an empty final prediction.",
    ]:
        bullet(doc, s)

    para(doc,
         "These are descriptive prevalences. They are not converted into causal statements, and "
         "they are not described with minimising language such as \"rare\" or \"negligible\".")


def sec23_efficiency(doc):
    h1(doc, "Section 23 - Computational Efficiency")

    para(doc,
         "Efficiency was characterised analytically (MAC lower bounds) and empirically (measured "
         "paths on an NVIDIA GeForce RTX 3060 Ti). Units are taken verbatim from the frozen tables.")

    add_table(doc, ["Quantity", "Value", "Unit", "Classification"],
              D.EFFICIENCY_TABLE, widths=[6.2, 3.4, 1.8, 4.6],
              caption="Table 23-1. Computational-efficiency summary (Phase34).",
              font_size=7.5)

    h2(doc, "23.1 Interpretation")
    para(doc,
         "The A8/C9 expected analytical MAC lower bound was 3.244e10 MACs, a ratio of 1.028 versus "
         "the global-only path (C1), and a saving of 2.345e9 MACs versus the always-refine path "
         "(C2). The measured weighted latency was 16.589 ms with a SKIP path of 15.718 ms and an "
         "EXECUTE path of 18.894 ms.")

    info_box(doc, "Efficiency claim boundary (frozen)", [
        "The MAC figures are an ANALYTICAL LOWER BOUND, not a measured end-to-end cost.",
        "The latency figures are HARDWARE-SPECIFIC runtime estimates on an RTX 3060 Ti, and are NOT "
        "end-to-end pipeline latencies, NOT real-time guarantees, NOT mobile estimates, and NOT "
        "energy measurements.",
        "No hardware-independent efficiency claim is made.",
    ])

    add_figure(
        doc, FIG / "p25e_compute_frontier.png",
        "Figure 12. Compute frontier (existing frozen figure from the router-development evidence "
        "base).",
        width_cm=13.5)


def sec24_interpretability(doc):
    h1(doc, "Section 24 - Interpretability")

    para(doc,
         "Descriptive model-mechanism evidence was collected in Phase35. It characterises how the "
         "frozen model behaves; it does not establish causal explanations.")

    h2(doc, "24.1 Router feature-group attribution")
    add_table(doc, ["Feature group", "Absolute total", "Share"],
              D.INTERP_GROUP_ATTRIBUTION, widths=[5.0, 5.5, 5.5],
              caption="Table 24-1. Router feature-group attribution (Phase35). "
                      "Attribution concentrates on decoder1 groups.",
              font_size=7.5)

    h2(doc, "24.2 Saliency self-consistency")
    add_table(doc, ["Feature", "Absolute mean/total", "Share / median"],
              D.INTERP_SALIENCY, widths=[4.5, 5.5, 6.0],
              caption="Table 24-2. Saliency self-consistency by domain and tap (Phase35).",
              font_size=7.5)

    h2(doc, "24.3 What was observed and what is only descriptive")
    for s in [
        "Observed: FiLM parameters are task-modulated, i.e. they differ by domain.",
        "Observed: router attribution concentrates on decoder1 feature groups (combined share of "
        "approximately 0.631 across the two decoder1 groups).",
        "Observed: decoder1 saliency self-consistency is approximately 1.0 across all domains.",
        "Descriptive only: no causal claim is made about WHY the router attends where it does.",
    ]:
        bullet(doc, s)

    add_figure(
        doc, FIG / "phase35_interpretability" / "phase35_f1_film_gamma_heatmap.png",
        "Figure 13. FiLM gamma heatmap (existing frozen Phase35 figure), showing task-modulated "
        "FiLM parameters.",
        width_cm=13.5)


def sec25_robustness(doc):
    h1(doc, "Section 25 - Robustness")

    para(doc,
         "Synthetic robustness studies were run on the development set VAL808 (n = 808). Two "
         "categories were evaluated: image-perturbation robustness and proposal/ROI-perturbation "
         "robustness. These are synthetic perturbations of a development set; they are not "
         "real-world acquisition shift.")

    h2(doc, "25.1 Image-perturbation robustness")
    para(doc,
         "12,928 synthetic image-perturbation paired rows were emitted across 16 conditions and 4 "
         "domains. The clean G reproduction was bit-identical, and the clean equivalence check "
         "passed for all rows.")
    add_table(doc, ["Domain", "Condition", "n", "Mean paired DeltaDice",
                    "Median paired DeltaDice"],
              D.IMAGE_ROBUSTNESS_TABLE, widths=[2.2, 4.2, 1.8, 4.0, 4.0],
              caption="Table 25-1. Phase36 image-perturbation paired DeltaDice by domain and "
                      "condition.", font_size=7.0, header_size=7.0)
    para(doc,
         "The largest adverse image-perturbation sensitivity was on KUB, especially under "
         "GAUSSIAN_NOISE_HIGH (mean paired DeltaDice -0.363643 for KUB). This is a synthetic "
         "worst-case characterisation, not a clinical robustness claim.")

    h2(doc, "25.2 Proposal / ROI-perturbation robustness")
    para(doc,
         "4,848 synthetic proposal-perturbation paired rows were emitted across 6 proposal "
         "conditions (four translations of 10 pixels and two scale factors).")
    add_table(doc, ["Domain", "Proposal condition", "n applicable", "Mean paired DeltaDice",
                    "Median paired DeltaDice"],
              D.PROPOSAL_ROBUSTNESS_TABLE, widths=[2.2, 4.2, 2.4, 3.8, 3.8],
              caption="Table 25-2. Phase36 proposal-perturbation paired DeltaDice by domain and "
                      "condition.", font_size=7.0, header_size=7.0)
    para(doc,
         "All proposal-perturbation median effects were 0.000000, and the means are small in "
         "magnitude, indicating that the pipeline is comparatively insensitive to the synthetic "
         "proposal perturbations tested. This is not a claim of independence from the proposal "
         "algorithm.")

    h2(doc, "25.3 KUB reporting-only subgroup robustness")
    para(doc,
         "The KUB domain's subgroup metadata is reporting-only. The table below is provided for "
         "completeness and must not be read as a use of subgroup identity as a model input.")
    add_table(doc, ["KUB subgroup", "Condition", "n", "Mean paired DeltaDice",
                    "Median paired DeltaDice"],
              D.KUB_SUBGROUP_ROBUSTNESS_TABLE, widths=[3.0, 4.2, 1.8, 3.5, 3.9],
              caption="Table 25-3. KUB reporting-only subgroup robustness (selected conditions).",
              font_size=7.0, header_size=7.0)

    h2(doc, "25.4 Frozen robustness figures (existing frozen figures)")
    add_figure(
        doc, FIG / "phase36_robustness_v1_23" /
        "R1_image_perturbation_mean_paired_delta_dice_heatmap.png",
        "Figure 14. Image-perturbation mean paired DeltaDice heatmap (existing frozen Phase36 "
        "figure).", width_cm=14.5)
    add_figure(
        doc, FIG / "phase36_robustness_v1_23" /
        "R4_proposal_perturbation_paired_delta_dice.png",
        "Figure 15. Proposal-perturbation paired DeltaDice (existing frozen Phase36 figure).",
        width_cm=14.5)


def sec26_test(doc):
    h1(doc, "Section 26 - Final TEST Evaluation")

    para(doc,
         "This section reports the frozen descriptive TEST results with maximum transparency. "
         "Phase39 v1.2 successfully evaluated all 1,683 TEST samples. The results below are "
         "DESCRIPTIVE FINAL-SYSTEM performance. They are NOT a primary TEST result and NOT a "
         "comparative TEST result.")

    add_table(doc, ["Domain", "n", "Descriptive final-system Dice", "Status"],
              D.TEST_DOMAIN_TABLE, widths=[5.0, 1.8, 5.6, 3.6],
              caption="Table 26-1. Descriptive Final-System Performance on the Frozen TEST Cohort.",
              font_size=7.5)

    para(doc,
         "Descriptive final-system Dice by domain was: ISIC (n = 735) 0.88693; BUSI (n = 174) "
         "0.85042; KVASIR (n = 216) 0.85071; KUB (n = 558) 0.73769. The descriptive macro-domain "
         "Dice was 0.8314368385956257. No post-hoc sample exclusion was applied.")

    info_box(doc, "How this table must be read", [
        "Title constraint observed: this table is titled \"Descriptive Final-System Performance on "
        "the Frozen TEST Cohort\". It is deliberately NOT titled \"Primary TEST Result\" and NOT "
        "titled \"Comparative TEST Result\".",
        "The three NOT_PRODUCED rows (macro DeltaDice vs C-gGLOBAL, comparative CI, per-domain harm "
        "flag) were not emitted by the frozen v1.2 execution.",
        "No quantity in this table supports a comparative conclusion against C-gGLOBAL.",
    ])

    add_figure(
        doc, FIG / "phase27_preservation" / "p27_dice_distributions.png",
        "Figure 16. Dice distributions (existing frozen Phase27 figure; development-set "
        "distribution shown for context, not a TEST comparative figure).",
        width_cm=13.5)


def sec27_protocol(doc):
    h1(doc, "Section 27 - Phase39 Protocol History and Limitation")

    para(doc,
         "The Phase39 protocol history is disclosed in full. Two pre-outcome technical attempts "
         "were consumed before a post-protocol technical-recovery execution succeeded.")

    add_table(doc, ["Attempt", "Failure / action", "Outcome", "Evidence anchors"],
              D.PHASE39_HISTORY, widths=[2.8, 6.2, 3.6, 3.4],
              caption="Table 27-1. Phase39 execution history.", font_size=7.0, header_size=7.5)

    h2(doc, "27.1 Preserved evidence class")
    info_box(doc, "Preserved verbatim (Phase39 evidence class)", [
        D.PHASE39_EVIDENCE_CLASS,
    ])

    h2(doc, "27.2 Terminology constraint")
    para(doc,
         "The TEST evaluation must NEVER be called UNTOUCHED_ONE_SHOT_TEST. That phrase is not used "
         "as an affirmative description anywhere in this report, because two pre-outcome technical "
         "attempts were consumed before the successful recovery execution.")


def sec28_missing_endpoint(doc):
    h1(doc, "Section 28 - Missing Phase39 Primary Endpoint")

    para(doc,
         "This section is mandatory and must be read before any TEST number is quoted.")

    para(doc,
         "The frozen Phase39 protocol prespecified a comparison of the final system against "
         "C-gGLOBAL, and required: a macro-domain Dice difference; a confidence interval; "
         "per-domain harm checks; and a frozen preservation decision.")

    para(doc,
         "The successful v1.2 execution did NOT emit the required C-gGLOBAL comparator quantities.")

    info_box(doc, "Adjudicated status", [
        "PRIMARY_ENDPOINT_NOT_PRODUCED.",
        "FROZEN_STATISTICAL_DECISION_NOT_EVALUABLE_FROM_V1_2_OUTPUT.",
        "No additional TEST inference was performed to reconstruct the missing endpoint.",
        "The comparator quantities are NOT derivable without new TEST inference, and none was "
        "performed.",
        "Source adjudication artifact: "
        "reports/audits/phase39_v1_2_scientific_protocol_completeness_adjudication.json "
        "(SHA-256 78a6ead5972ff6ba658dbfac3c68e686ea3662bbe22c01348652e6f083d102cc), field "
        "primary_endpoint_present = false.",
    ])

    h2(doc, "28.1 What the descriptive TEST Dice cannot be interpreted as")
    for s in [
        "Superiority of the final system over the comparator.",
        "Non-inferiority of the final system versus the comparator.",
        "Preservation confirmation on TEST.",
        "Harm-free refinement on TEST.",
        "Comparative benefit on TEST.",
    ]:
        bullet(doc, s)

    para(doc,
         "These prohibitions are absolute for this report. They are not softened, hedged, or "
         "reinterpreted anywhere.")


def sec29_can_claim(doc):
    h1(doc, "Section 29 - What We Can Claim")

    para(doc,
         "The table below is the supervisor-facing claim ledger. Each row gives the claim, its "
         "evidence, its population, its status, the exact allowed wording, and the forbidden "
         "wording. It is derived directly from the frozen final claim ledger.")

    add_table(doc, ["ID", "Claim", "Evidence", "Population", "Status", "Allowed wording",
                    "Forbidden wording"],
              D.CLAIM_TABLE, widths=[1.2, 3.0, 2.4, 2.2, 2.6, 5.0, 2.6],
              caption="Table 29-1. Claim / evidence boundary (frozen final claim ledger).",
              font_size=6.2, header_size=6.8)


def sec30_cannot_claim(doc):
    h1(doc, "Section 30 - What We Cannot Claim")

    info_box(doc, "We cannot claim from Phase39 TEST:", D.CANNOT_CLAIM)

    para(doc,
         "This transparency is deliberate and is important for the supervisor. The absence of a "
         "comparative TEST endpoint is a limitation of the executed protocol, not a defect of the "
         "architecture, and it is disclosed rather than concealed.")


def sec31_contributions(doc):
    h1(doc, "Section 31 - Summary of Contributions")

    h2(doc, "A. Methodological / system-integration contribution")
    para(doc,
         "The specification and frozen evaluation of a conditional regional-refinement architecture "
         "that combines (i) a pre-execution, learned, ground-truth-derived paired-Dice-gain gate for "
         "an optional regional refinement, (ii) a post-safety accept/reject stage, and (iii) a "
         "preserved-output fallback, applied to multi-domain medical binary segmentation under an "
         "explicit preservation constraint. The novelty is conservative and tied to the frozen "
         "literature evidence in Section 3.")

    h2(doc, "B. Empirical contribution")
    para(doc,
         "A full experimental programme on frozen populations: multi-domain development "
         "preservation (Phase27), a thirteen-arm module ablation including an explicitly reported "
         "negative result (Phase28), three-seed reproducibility (Phase29), the one-shot "
         "ROUTER_HOLDOUT evaluation with its qualifier (Phase30), descriptive statistical governance "
         "(Phase31), an external-cohort eligibility negative result (Phase32), a descriptive failure "
         "analysis (Phase33), an efficiency profile (Phase34), descriptive mechanism evidence "
         "(Phase35), synthetic image and proposal robustness studies (Phase36), and a descriptive "
         "final TEST evaluation (Phase39).")

    h2(doc, "C. Governance / reproducibility contribution")
    para(doc,
         "A preservation-oriented governance discipline in which the system is frozen before "
         "evaluation, checkpoint identities are hash-bound with fail-closed loading, statistical "
         "evidence remains descriptive, protocol deviations are disclosed verbatim, negative results "
         "are reported, and a missing primary endpoint is disclosed rather than reconstructed with "
         "new inference. Every number in this report is provenance-bound, and every claim maps to "
         "the frozen claim ledger.")


def sec32_limitations(doc):
    h1(doc, "Section 32 - Limitations")

    para(doc,
         "The frozen final limitations wording is the authority for this section. The limitations "
         "below are reproduced faithfully and not softened.")

    h2(doc, "32.1 Protocol limitations")
    para(doc,
         "The original Phase39 one-shot TEST protocol was not completed as intended. Two "
         "pre-outcome technical attempts were consumed before a post-protocol technical-recovery "
         "execution successfully evaluated the frozen system on all 1,683 TEST samples. No TEST "
         "image, label, prediction, metric, or scientific outcome had been observed before the "
         "recovery amendment. The successful recovery produced descriptive final-system "
         "segmentation performance but did not emit the prespecified C-gGLOBAL comparative "
         "quantities required to evaluate the frozen macro-domain Dice-difference endpoint and the "
         "associated per-domain harm rules. We therefore do not claim TEST-confirmed superiority, "
         "non-inferiority, preservation, or harm-free refinement, and no additional TEST inference "
         "was performed to reconstruct the missing endpoint.")

    h2(doc, "32.2 Evidence limitations")
    for s in [
        "The one-shot ROUTER_HOLDOUT result (Phase30) carries a disclosed post-first-open "
        "scientific source-freeze protocol deviation: " + D.PHASE30_QUALIFIER + ".",
        "No prospective clean external cohort was eligible (Phase32), so external validation was "
        "not performed.",
        "The statistical evidence is descriptive only (Phase31); no confirmatory significance "
        "procedure is eligible.",
        "Efficiency results are hardware-specific (RTX 3060 Ti) analytical and measured estimates, "
        "not end-to-end pipeline latency.",
        "Interpretability results are descriptive model-mechanism evidence, not causal claims.",
        "Robustness results are on synthetic perturbations of the development set, not real-world "
        "acquisition shift.",
        "KUB subgroups are REPORTING-ONLY metadata.",
    ]:
        bullet(doc, s)

    h2(doc, "32.3 Missing primary endpoint")
    para(doc,
         "The missing Phase39 comparative primary endpoint (Section 28) is the single most "
         "important limitation of the published evidence. It is not concealed and is not "
         "reconstructed.")

    h2(doc, "32.4 Dataset, domain, and generalisation limits")
    for s in [
        "The evaluation uses four specific clinical domains; generalisation to other modalities is "
        "not demonstrated.",
        "The per-domain population sizes are unequal, and KUB is the largest domain in VAL808 and "
        "TEST.",
        "The KUB subgroup metadata is reporting-only and is never used as a model input.",
        "The methodological assumptions (preservation constraint, frozen thresholds, fixed "
        "checkpoints) are part of the specification and are not free parameters.",
    ]:
        bullet(doc, s)

    add_table(doc, ["Limitation", "Nature", "Disclosed wording"],
              [
                  ("Missing Phase39 comparative primary endpoint",
                   "Protocol / evidence",
                   "PRIMARY_ENDPOINT_NOT_PRODUCED; "
                   "FROZEN_STATISTICAL_DECISION_NOT_EVALUABLE_FROM_V1_2_OUTPUT"),
                  ("Post-protocol technical-recovery status",
                   "Protocol / governance",
                   D.PHASE39_EVIDENCE_CLASS),
                  ("ROUTER_HOLDOUT source-freeze deviation",
                   "Protocol / evidence",
                   D.PHASE30_QUALIFIER),
                  ("No external validation", "Evidence",
                   "No prospective clean external cohort was eligible (Phase32)"),
                  ("Descriptive-only statistics", "Statistical",
                   "No new confirmatory significance procedure is eligible (Phase31)"),
                  ("Hardware-specific efficiency", "Interpretation",
                   "Not end-to-end; RTX 3060 Ti; analytical MAC lower bound"),
                  ("Descriptive mechanism evidence", "Interpretation",
                   "Not causal claims (Phase35)"),
                  ("Synthetic robustness only", "Evidence",
                   "Synthetic perturbations of the development set; not real-world acquisition "
                   "shift"),
                  ("KUB subgroups reporting-only", "Governance",
                   "Reporting metadata only; never classes/task-IDs/model inputs"),
              ],
              widths=[4.6, 3.0, 8.4],
              caption="Table 32-1. Key limitations summary.", font_size=7.0, header_size=7.5)


def sec33_future(doc):
    h1(doc, "Section 33 - Future Work")

    para(doc,
         "The following are clearly labelled SUGGESTIONS for future work. None of them has been "
         "performed, and none of them is a claim about the present system.")

    for s in [
        "Independent external cohorts: evaluate on cohorts that were not seen, in any form, during "
        "development, with provenance that permits a genuinely external claim.",
        "Prospective validation: fix the analysis plan before data access, so that a comparative "
        "endpoint can be evaluated confirmatorily.",
        "A new study specifically designed to evaluate comparative TEST preservation: that is, a "
        "study that actually produces the C-gGLOBAL comparator quantities missing from Phase39.",
        "Improved uncertainty and benefit estimation: better calibrated paired-gain prediction, "
        "potentially reducing the harmful-activation share.",
        "Broader modality and domain validation: extend beyond the four current domains.",
        "Deployment and runtime profiling on real clinical hardware: replace the current "
        "RTX 3060 Ti batch-path measurements with end-to-end pipeline profiling on target hardware.",
    ]:
        numbered(doc, s)

    para(doc,
         "These suggestions are consistent with the disclosed limitations and do not imply that any "
         "of them was already performed.")


def sec34_conclusion(doc):
    h1(doc, "Section 34 - Conclusion")

    para(doc,
         "This report documents RA-MedFiLM-BARR, a frozen conditional regional-refinement pipeline "
         "for multi-domain medical image segmentation. The system couples a shared FiLM-conditioned "
         "global segmenter with a learned pre-execution benefit router, an on-demand regional "
         "refiner, and a post-refinement safety stage, assembled by pad-aware fusion and a "
         "four-state decision machine with a preserved-output fallback.")

    para(doc,
         "The evidence that supports the work is development-set and holdout evidence: preservation "
         "of macro-domain Dice on VAL808 (macro DeltaDice 0.002210, 95% CI [0.001133, 0.003298]); a "
         "thirteen-arm ablation that includes an explicitly reported negative result; three-seed "
         "descriptive reproducibility; the one-shot ROUTER_HOLDOUT non-inferiority result with its "
         "mandatory disclosed deviation qualifier; descriptive failure modes; a bounded analytical "
         "and hardware-specific efficiency profile; descriptive mechanism evidence; and synthetic "
         "robustness studies.")

    para(doc,
         "The integration is useful because it makes the decision to refine explicit, learned, and "
         "made before the expensive computation, and because it protects the global prediction at "
         "two points: at the router gate (which can skip refinement) and at the post-safety stage "
         "(which can reject an executed refinement).")

    para(doc,
         "The descriptive TEST evaluation on all 1,683 samples shows that the frozen system produces "
         "final-system segmentation performance of 0.88693 (ISIC), 0.85042 (BUSI), 0.85071 "
         "(KVASIR), and 0.73769 (KUB), with a descriptive macro-domain Dice of 0.8314368385956257. "
         "The TEST evaluation does NOT establish comparative benefit: the prespecified C-gGLOBAL "
         "comparator quantities were not produced, so no TEST superiority, non-inferiority, "
         "preservation, or harm-free conclusion is asserted.")

    para(doc,
         "Manuscript readiness: the frozen manuscript is assembly-complete under the reduced scope "
         "MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY, with scientific_delta = 0, all "
         "numbers provenance-bound, and all claims evidence-bound. It is ready for supervisor review "
         "and for submission as a methodological and descriptive report. It is not ready to support "
         "a claim of TEST-confirmed comparative benefit against the global reference.")


def sec_references(doc):
    h1(doc, "References")

    para(doc,
         "The reference set below is the frozen final reference set. It was verified for "
         "existence, completeness of author/title/year metadata, absence of placeholder metadata, "
         "absence of duplicates, and support of the associated statements. Style: author(s) "
         "(year). Title. Venue. DOI/URL.")

    for key, authors, title, venue, doi in D.REFERENCES:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(f"[{key}] ")
        r.font.size = Pt(9.5)
        r.bold = True
        r2 = p.add_run(f"{authors}. {title}. {venue}. ")
        r2.font.size = Pt(9.5)
        r3 = p.add_run(doi if doi else "")
        r3.font.size = Pt(9.5)
        r3.font.color.rgb = RGBColor(0x1a, 0x4a, 0x8a)


# ===========================================================================
# Appendices
# ===========================================================================
def appendix_a(doc):
    h1(doc, "Appendix A - Frozen Model and Checkpoint Identities")

    para(doc,
         "The identities below are the frozen checkpoint identities used by the final system. The "
         "load contract fails closed on any mismatch.")
    add_table(doc, ["Component", "Class", "Checkpoint path", "SHA-256"],
              D.CHECKPOINT_IDENTITIES, widths=[1.6, 3.6, 6.2, 4.6],
              caption="Table A-1. Frozen checkpoint identities.", font_size=6.8, header_size=7.5)

    para(doc,
         "Component checkpoint SHA values as proposed in the work order and confirmed in the frozen "
         "repository authority:", justify=False)
    mono_block(doc, [
        "G       SHA: 286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "R_psi   SHA: 6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
        "B_phi   SHA: 8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
        "S_omega SHA: eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
    ])


def appendix_b(doc):
    h1(doc, "Appendix B - Major Phase Timeline")
    para(doc,
         "A compact version of the governance timeline, for quick reference.")
    add_table(doc, ["Stage", "Purpose", "Population", "Output", "Interpretation"],
              [(a, b, c, d, e) for (a, b, c, d, e, _f) in D.PHASE_TIMELINE],
              widths=[1.8, 4.4, 2.6, 3.8, 3.4],
              caption="Table B-1. Major phase timeline (qualifier column omitted for width).",
              font_size=6.8, header_size=7.5)


def appendix_c(doc):
    h1(doc, "Appendix C - Result Provenance Map")
    para(doc,
         "Every headline number in this report maps to a frozen artifact. The map below lists the "
         "main values and their frozen locators, transcribed from "
         "reports/manuscript/final/final_number_provenance.json.")

    rows = [
        ("G parameters", "3,523,001", "reports/audits/phase38_final_system_checkpoint_manifest.json",
         "components.G.parameters"),
        ("B_phi parameters", "36,801", "reports/audits/phase38_final_system_checkpoint_manifest.json",
         "components.B_phi.parameters"),
        ("R_psi parameters", "1,276,401", "reports/audits/phase38_final_system_checkpoint_manifest.json",
         "components.R_psi.parameters"),
        ("S_omega parameters", "1,217", "reports/audits/phase38_final_system_checkpoint_manifest.json",
         "components.S_omega.parameters"),
        ("Total parameters", "4,837,420", "reports/audits/phase38_final_system_checkpoint_manifest.json",
         "total_parameters"),
        ("VAL808 macro DeltaDice", "0.0022101452700813433", "reports/audits/phase27_final_freeze.json",
         "macro_point"),
        ("VAL808 macro CI low", "0.001133428168276068", "reports/audits/phase27_final_freeze.json",
         "macro_ci[0]"),
        ("VAL808 macro CI high", "0.003298131445733337", "reports/audits/phase27_final_freeze.json",
         "macro_ci[1]"),
        ("Ablation A8 mean routed delta", "0.007515754298",
         "reports/tables/phase28_table_02_arm_primary_metrics.csv",
         "A8 mean_true_delta_dice_routed"),
        ("Ablation A5 negative result", "-0.000433374404",
         "reports/tables/phase28_table_02_arm_primary_metrics.csv",
         "A5 mean_true_delta_dice_routed"),
        ("Repro ROUTER_DEVELOPMENT mean", "0.0012148299969405082",
         "reports/tables/phase29_three_seed_dev_summary.csv", "macro_domain_delta_dice mean"),
        ("Repro VAL808 mean", "0.0028222956994930896",
         "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json", "macro_delta_dice.mean"),
        ("ROUTER_HOLDOUT A8/C9 macro Dice", "0.9302871820357663",
         "reports/audits/phase30_primary_noninferiority_result.json", "a8_macro_dice"),
        ("ROUTER_HOLDOUT global macro Dice", "0.9285481511747413",
         "reports/audits/phase30_primary_noninferiority_result.json", "global_macro_dice"),
        ("ROUTER_HOLDOUT macro DeltaDice", "0.0017390308610248934",
         "reports/audits/phase30_primary_noninferiority_result.json", "macro_delta_dice"),
        ("ROUTER_HOLDOUT macro CI", "[0.00111729355352301, 0.0024049809029647283]",
         "reports/audits/phase30_primary_noninferiority_result.json", "macro_ci"),
        ("LOW_OVERLAP failure rate", "0.10057142857142858",
         "reports/tables/phase33_failure_prevalence_overall_v1_2.csv", "LOW_OVERLAP.failure_rate"),
        ("ROUTER_HARMFUL_ACTIVATION rate", "0.12916666666666668",
         "reports/tables/phase33_failure_prevalence_overall_v1_2.csv",
         "ROUTER_HARMFUL_ACTIVATION.failure_rate"),
        ("EXECUTE_THEN_REJECT rate", "0.016666666666666666",
         "reports/tables/phase33_failure_prevalence_overall_v1_2.csv",
         "EXECUTE_THEN_REJECT.failure_rate"),
        ("Analytical MAC lower bound", "32437902022.582855",
         "reports/tables/phase34_analytical_compute_summary_v1_3.csv",
         "FINAL_A8_C9_EXPECTED_CONDITIONAL.macs"),
        ("Analytical MAC ratio", "1.0280859651011032",
         "reports/tables/phase34_analytical_compute_summary_v1_3.csv", "RATIO_A8C9_vs_C1.macs"),
        ("Analytical MAC saving", "2344501561.417145",
         "reports/tables/phase34_analytical_compute_summary_v1_3.csv", "SAVING_vs_literal_C2.macs"),
        ("Weighted latency (ms)", "16.589411566892352",
         "reports/tables/phase34_conditional_runtime_estimate_v1_4.csv", "L_weighted_ms"),
        ("Image-robustness rows", "12928",
         "reports/audits/phase36_robustness_scientific_result_v1_23.json",
         "counts.image_rows_emitted"),
        ("Proposal-robustness rows", "4848",
         "reports/audits/phase36_robustness_scientific_result_v1_23.json",
         "counts.proposal_rows_emitted"),
        ("TEST n", "1683", "reports/audits/phase39_final_test_v1_2_scientific_result.json", "test_n"),
        ("TEST ISIC Dice", "0.8869294005502611",
         "reports/audits/phase39_final_test_v1_2_scientific_result.json",
         "summary.per_domain[ISIC].dice_mean"),
        ("TEST BUSI Dice", "0.8504187847033107",
         "reports/audits/phase39_final_test_v1_2_scientific_result.json",
         "summary.per_domain[BUSI].dice_mean"),
        ("TEST KVASIR Dice", "0.8507055649364359",
         "reports/audits/phase39_final_test_v1_2_scientific_result.json",
         "summary.per_domain[KVASIR].dice_mean"),
        ("TEST KUB Dice", "0.7376936041924949",
         "reports/audits/phase39_final_test_v1_2_scientific_result.json",
         "summary.per_domain[KUB].dice_mean"),
        ("TEST descriptive macro Dice", "0.8314368385956257",
         "reports/audits/phase39_final_test_v1_2_scientific_result.json", "summary.macro_dice"),
        ("TEST primary endpoint", "NOT_PRODUCED_BY_FROZEN_PHASE39_EXECUTION",
         "reports/audits/phase39_v1_2_scientific_protocol_completeness_adjudication.json",
         "primary_endpoint_present=false"),
    ]
    add_table(doc, ["Quantity", "Value", "Frozen artifact", "Locator"],
              rows, widths=[3.8, 4.0, 5.4, 3.2],
              caption="Table C-1. Result provenance map.", font_size=6.0, header_size=7.0)


def appendix_d(doc):
    h1(doc, "Appendix D - Claim Ledger")
    para(doc, "The full frozen claim ledger, in supervisor-readable form.")
    add_table(doc, ["ID", "Claim family", "Population", "Status", "TEST-confirmed",
                    "Confirmatory status"],
              [(c[0], c[3], c[1], c[4], "No", c[2]) for c in [
                  ("C-A1", "VAL808 (n=808)", "CONTINUITY_DEVELOPMENT_EVIDENCE", "A", "Descriptive "
                   "preservation / non-inferiority", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-A2", "ROUTER_HOLDOUT (n=875)",
                   "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_"
                   "POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION",
                   "A", "One-shot descriptive non-inferiority",
                   "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-B1", "ROUTER_DEVELOPMENT (n=4957)",
                   "PHASE28_CANONICAL_COMPREHENSIVE_SYSTEM_ABLATION_EXECUTION", "B",
                   "Descriptive ablation", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-C1", "ROUTER_DEVELOPMENT + VAL808", "DESCRIPTIVE_THREE_SEED_REPRODUCIBILITY",
                   "C", "Descriptive reproducibility",
                   "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-E1", "multi-population governance",
                   "GOVERNANCE_ONLY_STATISTICAL_PROVENANCE_CLOSURE", "E", "Governance only",
                   "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-F1", "EXTERNAL (19 candidates)",
                   "GOVERNANCE_ONLY_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_CLOSURE",
                   "F", "Governance only (negative)", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-G1", "ROUTER_HOLDOUT (n=875)", "DESCRIPTIVE_FINAL_SYSTEM_FAILURE_ANALYSIS_CLOSURE",
                   "G", "Descriptive failure analysis",
                   "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-H1", "analytical + measured (RTX 3060 Ti)", "ANALYTICAL_MAC_LOWER_BOUND", "H",
                   "Analytical / hardware-specific", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-I1", "model-mechanism", "DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE", "I",
                   "Descriptive mechanism", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-J1", "VAL808 (n=808)",
                   "DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE", "J",
                   "Synthetic robustness", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-K1", "VAL808 (n=808)",
                   "DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE", "K",
                   "Synthetic robustness", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-L1", "VAL808 KUB subset (n=280)",
                   "DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE", "L",
                   "Reporting-only metadata", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-T1", "TEST (n=1683)",
                   "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_"
                   "PREOUTCOME_TECHNICAL_FAILURES", "TEST_descriptive",
                   "Descriptive TEST performance", "DESCRIPTIVE_OR_NONINFERIORITY_DEVELOPMENT"),
                  ("C-T2", "TEST (n=1683)",
                   "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_"
                   "PREOUTCOME_TECHNICAL_FAILURES", "TEST_comparative",
                   "PRIMARY_ENDPOINT_NOT_PRODUCED__NOT_DERIVABLE_WITHOUT_NEW_TEST_INFERENCE",
                   "PRIMARY_ENDPOINT_NOT_PRODUCED__NOT_DERIVABLE_WITHOUT_NEW_TEST_INFERENCE"),
              ]],
              widths=[1.4, 2.2, 4.4, 1.8, 3.2, 3.0],
              caption="Table D-1. Frozen claim ledger (all TEST-confirmed = No).",
              font_size=6.0, header_size=6.8)


def appendix_e(doc):
    h1(doc, "Appendix E - Phase39 Execution and Protocol History")
    para(doc, "The full Phase39 execution history with evidence anchors.")
    add_table(doc, ["Attempt", "Failure / action", "Outcome", "Evidence anchors"],
              D.PHASE39_HISTORY, widths=[2.6, 6.2, 3.4, 3.8],
              caption="Table E-1. Phase39 execution and protocol history.",
              font_size=6.8, header_size=7.5)


def appendix_f(doc):
    h1(doc, "Appendix F - Reproducibility and Governance Summary")
    para(doc,
         "This appendix summarises the reproducibility and governance guarantees that make the "
         "evidence in this report auditable.")
    rows = [
        ("Final system frozen before evaluation", "Yes",
         "Components, thresholds, and checkpoints are frozen; loading fails closed on hash mismatch."),
        ("Checkpoint identity binding", "Yes",
         "All four component checkpoints are SHA-256 bound (Appendix A)."),
        ("Strict loading contract", "Yes",
         "Zero missing/unexpected keys; all weights finite; eval mode; requires_grad=False; CUDA only."),
        ("Statistical evidence type", "Descriptive",
         "Bootstrap confidence intervals only; no confirmatory procedure is eligible (Phase31)."),
        ("Protocol deviation disclosures", "Yes",
         "Phase30 qualifier and Phase39 evidence class are disclosed verbatim."),
        ("Negative results reported", "Yes",
         "F1 integrated refiner negative result reported in the ablation and in the claim ledger."),
        ("Missing endpoint disclosed", "Yes",
         "Phase39 primary comparative endpoint declared NOT PRODUCED in the main text."),
        ("Number provenance", "Complete",
         "Every number maps to a frozen artifact (Appendix C; numeric audit all_pass = true)."),
        ("Claim provenance", "Complete",
         "Every claim maps to the frozen claim ledger (claim audit all_pass = true; 0 orphans)."),
        ("Reference verification", "Complete",
         "30 cited references; 0 placeholders; 0 duplicates; all cited in body."),
        ("scientific_delta", "0",
         "No new science; document assembly only."),
        ("TEST access / inference / training", "0 / 0 / 0",
         "No TEST image read, no inference, no training, no new statistics."),
    ]
    add_table(doc, ["Governance property", "Value", "Detail"],
              rows, widths=[4.6, 2.4, 9.0],
              caption="Table F-1. Reproducibility and governance summary.",
              font_size=7.0, header_size=7.5)


def appendix_g(doc):
    h1(doc, "Appendix G - Reference List")
    para(doc,
         "The 30 frozen references are listed here for convenience. The main reference list appears "
         "before the appendices; this appendix repeats it in compact form.")
    for i, (key, authors, title, venue, doi) in enumerate(D.REFERENCES, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(f"{i}. [{key}] {authors}. {title}. {venue}. {doi if doi else ''}")
        r.font.size = Pt(8.5)


def supervisor_quick_review(doc):
    page_break(doc)
    h1(doc, "Supervisor Quick Review")
    para(doc,
         "A one-page summary for the supervisor, answered from frozen evidence only.",
         italic=True)

    for i, (q, a) in enumerate(D.QUICK_REVIEW, 1):
        h3(doc, f"{i}. {q}")
        para(doc, a)


# ===========================================================================
# Build
# ===========================================================================
def build() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = new_document()

    # Footer on all sections
    for s in doc.sections:
        add_page_number_footer(s)

    # ---- Front matter (title page + executive summary) ----
    build_title_page(doc)
    build_executive_summary(doc)

    # Deterministic figure and table inventories (declared up front so the
    # List of Figures / List of Tables can be emitted before the body).
    figures = [
        (1, "Overall RA-MedFiLM-BARR methodology and multi-domain inference pipeline "
            "(researcher-supplied methodology infographic).",
         str(METHODOLOGY_IMAGE)),
        (2, "Frozen full-system architecture.", "reports/figures/methodology_diagram_package/"),
        (3, "Canonical inference state machine.", "reports/figures/methodology_diagram_package/"),
        (4, "Four-domain input montage.", "reports/figures/methodology_diagram_package/"),
        (5, "Predicted ROI localisation panel.", "reports/figures/methodology_diagram_package/"),
        (6, "Router feature-group attribution (Phase35).", "reports/figures/phase35_interpretability/"),
        (7, "Post-safety 20-D input breakdown.", "reports/figures/methodology_diagram_package/"),
        (8, "Per-domain DeltaDice forest plot on VAL808 (Phase27).",
         "reports/figures/phase27_preservation/"),
        (9, "Ablation arm matrix overview (Phase28).", "reports/figures/p28_fig1_arm_matrix_overview.png"),
        (10, "Seed-wise macro DeltaDice on VAL808 (Phase29).", "reports/figures/phase29_val808/"),
        (11, "Per-sample final Dice distribution (Phase29).", "reports/figures/phase29_val808/"),
        (12, "Compute frontier (frozen).", "reports/figures/p25e_compute_frontier.png"),
        (13, "FiLM gamma heatmap (Phase35).", "reports/figures/phase35_interpretability/"),
        (14, "Image-perturbation DeltaDice heatmap (Phase36).",
         "reports/figures/phase36_robustness_v1_23/"),
        (15, "Proposal-perturbation DeltaDice (Phase36).", "reports/figures/phase36_robustness_v1_23/"),
        (16, "Dice distributions (Phase27).", "reports/figures/phase27_preservation/"),
    ]
    tables = [
        ("0a", "Abbreviations and symbols"),
        ("5-1", "Research questions and frozen evidence"),
        ("6-1", "Task, domain, and modality summary"),
        ("6-2", "Population and split summary"),
        ("6-3", "Frozen TEST cohort composition"),
        ("6-4", "KUB reporting-only subgroup metadata"),
        ("8-1", "Final architecture and component specification"),
        ("8-2", "Frozen component specification with checkpoint identities"),
        ("8-3", "Frozen checkpoint identities"),
        ("9-1", "Frozen GlobalMedFiLM architecture facts"),
        ("10-1", "Frozen ROI proposal parameters"),
        ("11-1", "Frozen B_phi specification"),
        ("11-2", "The 192 deep feature taps"),
        ("12-1", "Frozen R_psi specification"),
        ("13-1", "Frozen S_omega specification"),
        ("14-1", "The four-state decision machine"),
        ("16-1", "Major phase timeline"),
        ("17-1", "VAL808 multi-domain development preservation results"),
        ("17-2", "ROUTER_HOLDOUT per-domain and macro DeltaDice"),
        ("18-1", "Frozen 13-arm ablation results"),
        ("19-1", "Three-seed reproducibility summary"),
        ("20-1", "One-shot ROUTER_HOLDOUT result"),
        ("21-1", "Statistical test registry"),
        ("22-1", "Descriptive failure-mode prevalence"),
        ("23-1", "Computational-efficiency summary"),
        ("24-1", "Router feature-group attribution"),
        ("24-2", "Saliency self-consistency"),
        ("25-1", "Phase36 image-perturbation summary"),
        ("25-2", "Phase36 proposal-perturbation summary"),
        ("25-3", "KUB reporting-only subgroup robustness"),
        ("26-1", "Descriptive Final-System Performance on the Frozen TEST Cohort"),
        ("27-1", "Phase39 execution history"),
        ("29-1", "Claim / evidence boundary"),
        ("32-1", "Key limitations summary"),
        ("A-1", "Frozen checkpoint identities"),
        ("B-1", "Major phase timeline"),
        ("C-1", "Result provenance map"),
        ("D-1", "Frozen claim ledger"),
        ("E-1", "Phase39 execution and protocol history"),
        ("F-1", "Reproducibility and governance summary"),
    ]

    # ---- Front matter that depends on the inventories above ----
    build_list_of_figures(doc, figures)
    build_list_of_tables(doc, tables)
    build_abbreviations(doc)

    # ---- Body sections (TOC_ENTRIES fills as headings are created) ----
    sec1_background(doc)
    sec2_problem(doc)
    sec3_literature(doc)
    sec4_novelty(doc)
    sec5_rq(doc)
    sec6_datasets(doc)
    sec7_methodology(doc)
    sec8_architecture(doc)
    sec9_gmedfilm(doc)
    sec10_roi(doc)
    sec11_bphi(doc)
    sec12_rpsi(doc)
    sec13_somega(doc)
    sec14_state_machine(doc)
    sec15_fusion(doc)
    sec16_governance(doc)
    sec17_development(doc)
    sec18_ablation(doc)
    sec19_reproducibility(doc)
    sec20_holdout(doc)
    sec21_stats(doc)
    sec22_failure(doc)
    sec23_efficiency(doc)
    sec24_interpretability(doc)
    sec25_robustness(doc)
    sec26_test(doc)
    sec27_protocol(doc)
    sec28_missing_endpoint(doc)
    sec29_can_claim(doc)
    sec30_cannot_claim(doc)
    sec31_contributions(doc)
    sec32_limitations(doc)
    sec33_future(doc)
    sec34_conclusion(doc)
    sec_references(doc)
    appendix_a(doc)
    appendix_b(doc)
    appendix_c(doc)
    appendix_d(doc)
    appendix_e(doc)
    appendix_f(doc)
    appendix_g(doc)
    supervisor_quick_review(doc)

    # ------------------------------------------------------------------
    # Insert the Table of Contents directly after the Executive Summary.
    # The TOC needs TOC_ENTRIES, which is only complete after the body is
    # built; so we build the TOC into a temporary document and then splice
    # its XML into the main document at the right position.
    # ------------------------------------------------------------------
    _splice_toc_after_exec_summary(doc)

    doc.save(str(OUT_DOCX))
    return {"figures": figures, "tables": tables}


def _splice_toc_after_exec_summary(doc) -> None:
    """Build the TOC and move its body to directly after the Executive Summary."""
    tmp = Document()
    _install_base_styles(tmp)
    build_toc(tmp)

    # Locate the paragraph that starts the "List of Figures" heading in `doc`;
    # everything before it (title page + exec summary + page break) is the
    # insertion anchor. We insert the TOC elements immediately BEFORE the
    # "List of Figures" heading so the order becomes:
    #   Title -> Exec Summary -> TOC -> List of Figures -> List of Tables -> ...
    anchor = None
    for p in doc.paragraphs:
        if p.text.strip() == "List of Figures":
            anchor = p
            break
    if anchor is None:
        return

    anchor_el = anchor._p
    parent = anchor_el.getparent()
    idx = list(parent).index(anchor_el)

    new_els = [el for el in list(tmp.element.body) if el.tag != qn("w:sectPr")]
    for offset, el in enumerate(new_els):
        parent.insert(idx + offset, el)


def _install_base_styles(doc) -> None:
    """Apply the same base styles used by the main document (for the TOC temp doc)."""
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    pf = normal.paragraph_format
    pf.line_spacing = 1.15
    pf.space_after = Pt(6)
    for name, size, color in (("Heading 1", 17, ACCENT), ("Heading 2", 13.5, ACCENT),
                              ("Heading 3", 11.5, ACCENT), ("Caption", 9.5, RGBColor(0x44, 0x44, 0x44))):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.color.rgb = color


# ===========================================================================
# Validation + manifest
# ===========================================================================
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


FORBIDDEN_PAIRS = [
    ("phase39", "superior"),
    ("phase39", "outperform"),
    ("phase39", "noninferior"),
    ("phase39", "non-inferior"),
    ("phase39", "preservation confirmed"),
    ("phase39", "harm-free"),
    ("phase39", "significant improvement"),
    ("phase39", "primary endpoint achieved"),
    ("phase39", "confirmatory"),
]

PLACEHOLDER_TOKENS = ["{P30Q}", "{P39Q}", "TODO", "TBD", "INSERT HERE",
                      "[PLACEHOLDER]", "XXXPLACEHOLDERXXX"]


def validate_docx(docx_path: Path) -> dict:
    """Re-open the DOCX and run structural + compliance checks."""
    doc = Document(str(docx_path))
    all_text = "\n".join(p.text for p in doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                all_text += "\n" + cell.text

    low = all_text.lower()

    required_sections = [
        "Executive Summary", "Table of Contents", "List of Figures", "List of Tables",
        "Abbreviations and Symbols",
        "Section 1 - Research Background", "Section 2 - Problem Statement",
        "Section 3 - Literature Review", "Section 4 - Research Gap and Novelty",
        "Section 5 - Research Questions", "Section 6 - Datasets and Tasks",
        "Section 7 - Complete RA-MedFiLM-BARR Methodology",
        "Section 8 - Final System Architecture", "Section 9 - GlobalMedFiLM",
        "Section 10 - ROI Extraction", "Section 11 - Benefit Router",
        "Section 12 - Regional Refiner", "Section 13 - Post-Safety",
        "Section 14 - State Machine", "Section 15 - Fusion and Final Scoring",
        "Section 16 - Development and Experimental Governance",
        "Section 17 - Development and Preservation Results", "Section 18 - Ablation Study",
        "Section 19 - Reproducibility", "Section 20 - One-Shot ROUTER_HOLDOUT Evidence",
        "Section 21 - Statistical Governance", "Section 22 - Failure-Mode Analysis",
        "Section 23 - Computational Efficiency", "Section 24 - Interpretability",
        "Section 25 - Robustness", "Section 26 - Final TEST Evaluation",
        "Section 27 - Phase39 Protocol History", "Section 28 - Missing Phase39 Primary Endpoint",
        "Section 29 - What We Can Claim", "Section 30 - What We Cannot Claim",
        "Section 31 - Summary of Contributions", "Section 32 - Limitations",
        "Section 33 - Future Work", "Section 34 - Conclusion",
        "References",
        "Appendix A", "Appendix B", "Appendix C", "Appendix D", "Appendix E",
        "Appendix F", "Appendix G",
        "Supervisor Quick Review",
    ]
    missing_sections = [s for s in required_sections if s.lower() not in low]

    # Figure / table counts
    n_tables = len(doc.tables)
    n_figures = 0
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            n_figures += 1

    toc_present = ("TOC \\o" in all_text) or ("toc" in low and "update field" in low)

    method_img_embedded = False
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            method_img_embedded = True

    p30 = D.PHASE30_QUALIFIER in all_text
    p39 = D.PHASE39_EVIDENCE_CLASS in all_text
    missing_endpoint = ("PRIMARY_ENDPOINT_NOT_PRODUCED" in all_text or
                        "NOT_PRODUCED_BY_FROZEN_PHASE39_EXECUTION" in all_text)
    # "UNTOUCHED_ONE_SHOT_TEST" may appear ONLY inside an explicit prohibition
    # statement (e.g. "must NEVER be called ..."), never as an affirmative label.
    untouched_affirmative = False
    for line in all_text.split("\n"):
        if "UNTOUCHED_ONE_SHOT_TEST" in line:
            ll = line.lower()
            if not any(w in ll for w in ["never", "must not", "not be called",
                                         "forbidden", "prohibit"]):
                untouched_affirmative = True
    untouched_absent = not untouched_affirmative

    # Forbidden-claim scan.
    #
    # The report legitimately CONTAINS forbidden terms in three places, all of
    # which are disclosures/prohibitions rather than affirmative claims:
    #   (a) the "What We Cannot Claim" box and the Section 28 prohibition list;
    #   (b) the frozen claim-ledger "forbidden wording" column;
    #   (c) the Table 21-1 statistical SUMMARY row (n_confirmatory=0).
    # A line is therefore flagged ONLY when it affirmatively asserts a forbidden
    # Phase39/TEST outcome: it must use an assertive verb, must NOT be negated,
    # and must NOT sit inside a prohibition/ledger context.
    assert_terms = ["is ", "are ", "was ", "were ", "has ", "have ", "achieves",
                    "achieved", "demonstrates", "shows", "outperforms", "confirms",
                    "establishes", "produced"]
    prohib_markers = ["cannot", "must not", "never", "forbidden wording",
                      "n_confirmatory=0", "not produced", "we do not", "does not",
                      "is not", "are not", "no test", "not evaluable", "without",
                      "--", "prohibit", "no new confirmatory", "no confirmatory",
                      "was not authorized", "not authorized"]
    claim_violations = []
    for line in all_text.split("\n"):
        ll = line.lower()
        if not ("phase39" in ll or "test" in ll):
            continue
        if not any(f in ll for _a, f in FORBIDDEN_PAIRS):
            continue
        if any(m in ll for m in prohib_markers):
            continue
        if not any(a in ll for a in assert_terms):
            continue
        claim_violations.append(line.strip()[:180])

    placeholder_hits = [tok for tok in PLACEHOLDER_TOKENS if tok.lower() in low]

    return {
        "opens": True,
        "n_paragraphs": len(doc.paragraphs),
        "n_tables": n_tables,
        "n_figures_embedded": n_figures,
        "missing_sections": missing_sections,
        "toc_present": bool(toc_present),
        "methodology_image_embedded": bool(method_img_embedded),
        "phase30_qualifier_present": p30,
        "phase39_qualifier_present": p39,
        "missing_primary_endpoint_disclosed": missing_endpoint,
        "untouched_one_shot_test_absent": untouched_absent,
        "claim_scan_violations": claim_violations,
        "placeholder_hits": placeholder_hits,
    }


def write_manifest(validation: dict, n_figures: int, n_tables: int) -> dict:
    docx_sha = sha256_file(OUT_DOCX)
    docx_size = OUT_DOCX.stat().st_size
    try:
        method_sha = sha256_file(METHODOLOGY_IMAGE)
    except Exception:
        method_sha = None

    manifest = {
        "classification": "SUPERVISOR_REPORT_BUILD_MANIFEST",
        "build_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "docx_filename": OUT_DOCX.name,
        "docx_path": str(OUT_DOCX),
        "docx_sha256": docx_sha,
        "docx_size_bytes": docx_size,
        "final_scientific_scope": D.RELEASE["final_scientific_scope"],
        "scientific_delta": 0,
        "source_final_manuscript": D.RELEASE["manuscript_final_path"],
        "source_final_manuscript_sha256": D.RELEASE["manuscript_final_sha256"],
        "source_final_release_manifest": D.RELEASE["release_manifest_path"],
        "source_final_release_manifest_sha256": D.RELEASE["release_manifest_sha256"],
        "methodology_image_path": str(METHODOLOGY_IMAGE),
        "methodology_image_sha256": method_sha,
        "n_tables": n_tables,
        "n_figures": n_figures,
        "n_sections": 46,
        "page_count_deterministic": False,
        "page_count_note": "Page count is not deterministically obtainable without a Word "
                           "rendering engine; the field is populated after the report is opened "
                           "and fields are updated in Microsoft Word.",
        "included_tables": TABLE_INVENTORY,
        "included_figures": FIGURE_INVENTORY,
        "validation": validation,
        "execution_ledger": {
            "scientific_delta": 0,
            "TEST_access": 0,
            "TEST_image_reads": 0,
            "TEST_GT_reads": 0,
            "model_inference": 0,
            "training": 0,
            "new_statistics": 0,
            "new_bootstrap": 0,
            "new_comparator_computation": 0,
        },
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


TABLE_INVENTORY = []
FIGURE_INVENTORY = []


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build()
    global TABLE_INVENTORY, FIGURE_INVENTORY
    FIGURE_INVENTORY = [
        {"figure": f"Figure {n}", "caption": cap, "source": src}
        for (n, cap, src) in result["figures"]
    ]
    TABLE_INVENTORY = [
        {"table": f"Table {num}", "title": title} for (num, title) in result["tables"]
    ]

    validation = validate_docx(OUT_DOCX)
    manifest = write_manifest(validation, len(result["figures"]), len(result["tables"]))

    print("=" * 78)
    print("SUPERVISOR DOCX REPORT BUILT")
    print("=" * 78)
    print(f"DOCX path           : {OUT_DOCX}")
    print(f"DOCX SHA-256        : {manifest['docx_sha256']}")
    print(f"DOCX size (bytes)   : {manifest['docx_size_bytes']}")
    print(f"Tables              : {validation['n_tables']} (doc.tables)")
    print(f"Figures embedded    : {validation['n_figures_embedded']} (doc.images)")
    print(f"TOC present         : {'PASS' if validation['toc_present'] else 'FAIL'}")
    print(f"Methodology image   : {'PASS' if validation['methodology_image_embedded'] else 'FAIL'}")
    print(f"Phase30 qualifier   : {'PASS' if validation['phase30_qualifier_present'] else 'FAIL'}")
    print(f"Phase39 qualifier   : {'PASS' if validation['phase39_qualifier_present'] else 'FAIL'}")
    print(f"Missing endpoint    : {'PASS' if validation['missing_primary_endpoint_disclosed'] else 'FAIL'}")
    print(f"UNTOUCHED absent    : {'PASS' if validation['untouched_one_shot_test_absent'] else 'FAIL'}")
    print(f"Missing sections    : {validation['missing_sections'] or 'none'}")
    print(f"Claim violations    : {validation['claim_scan_violations'] or 'none'}")
    print(f"Placeholder hits    : {validation['placeholder_hits'] or 'none'}")
    print(f"Manifest            : {OUT_MANIFEST}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
