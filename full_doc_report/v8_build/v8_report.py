"""ReMedFiLM V8 -- report generator (DOCX).

Builds ``ReMedFiLM_Complete_Scientific_Report_V8.docx`` from:

  * REMEDFILM_V8_RESULTS_REGISTRY.json   (single numeric source, 291 records)
  * REMEDFILM_V8_FIGURE_EVIDENCE_MAP.json (33 figures, all SHA-verified)
  * REMEDFILM_V8_RESULT_RECONCILIATION.md (adjudication narrative)

Design contract
---------------
A4 portrait, Times New Roman body / Arial display, white figures with navy
text, blue = GlobalMedFiLM, teal = ReMedFiLM FULL, minimal horizontal-only
table rules, captions OUTSIDE images, sequentially numbered figures and
tables from one global counter (V7's duplicate internal numbering removed).

Every number printed in prose or a table is fetched from the registry through
``M()``; no numeric result is typed by hand. The one deliberate exception is
the V7 hard-coded triplet, which is preserved ONLY as an adjudication exhibit
and is explicitly labelled as rejected.

The PDF is produced from this DOCX by Word COM (see export_v8_pdf.ps1), so
DOCX and PDF are identical by construction rather than by two renderers.

Analysis-only: no training, no inference, no checkpoint writes, TEST1683
inputs are never opened.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from v8_common import FDR, ROOT, sha256, write_json

# --------------------------------------------------------------------------- #
# paths / data
# --------------------------------------------------------------------------- #
REG = json.loads((FDR / "REMEDFILM_V8_RESULTS_REGISTRY.json").read_text(encoding="utf-8"))
EMAP = json.loads((FDR / "REMEDFILM_V8_FIGURE_EVIDENCE_MAP.json").read_text(encoding="utf-8"))
ARROWS = json.loads((FDR / "REMEDFILM_V8_METHODOLOGY_ARROWS.json").read_text(encoding="utf-8"))
COMPONENTS = json.loads((FDR / "REMEDFILM_FULL_COMPONENT_REGISTRY.json").read_text(encoding="utf-8"))

OUT_DOCX = FDR / "ReMedFiLM_Complete_Scientific_Report_V8.docx"
MANIFEST = FDR / "V8_REPORT_CONTENT_MANIFEST.json"

_METRICS = {m["metric_id"]: m for m in REG["metrics"]}


def M(mid: str):
    """Fetch a registry value by metric_id. A missing key is a hard error.

    Deliberately no ``or`` fallback: an unresolvable registry key must abort.
    """
    if mid not in _METRICS:
        raise KeyError(f"registry key absent -- ABORT: {mid}")
    return _METRICS[mid]["value"]


def f4(x, nd: int = 4) -> str:
    return f"{float(x):.{nd}f}"


FIG_PATH: dict[str, Path] = {}
for _f in EMAP["figures"]:
    if "files" in _f:
        _p = FDR / _f["files"]["png"]["path"]
    else:
        _p = ROOT / _f["png_path"]
    if not _p.exists():
        raise FileNotFoundError(_p)
    FIG_PATH[_f["figure_id"]] = _p

SECTION_TITLES = [
    "Overview and contributions",
    "Methodology: the proposed ReMedFiLM FULL system",
    "Datasets, splits and evaluation protocol",
    "Internal quantitative results",
    "Training history and staged objectives",
    "Real segmentation results",
    "Class and subclass performance",
    "External retrospective evaluation",
    "Component progression and ablation",
    "Routing, safety and error propagation",
    "Reproducibility, interpretability and robustness",
    "Computational complexity and accuracy-cost",
    "Conclusions, limitations and next experiments",
]

# --------------------------------------------------------------------------- #
# design system
# --------------------------------------------------------------------------- #
NAVY = RGBColor(0x1B, 0x36, 0x5D)
BLUE = RGBColor(0x2B, 0x6C, 0xB0)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
GREY = RGBColor(0x55, 0x63, 0x70)
BODY = RGBColor(0x1A, 0x22, 0x30)
RED = RGBColor(0xB3, 0x2D, 0x2E)
AMBER = RGBColor(0xB8, 0x7A, 0x12)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = "EAF0F7"
LIGHTER = "F5F8FC"

SERIF = "Times New Roman"
SANS = "Arial"
MONO = "Consolas"

WIDTH = 158.0          # nominal figure width, mm
FIG_SCALE = 0.92       # single global knob applied to every figure width
TEXT_W = 170.0         # A4 210 mm - 2 x 20 mm

# --------------------------------------------------------------------------- #
# low-level XML helpers
# --------------------------------------------------------------------------- #
def _el(tag: str):
    return OxmlElement(tag)


# ECMA-376 child-order successors. python-docx exposes no get_or_add helper for
# borders / shading, and a plain ``append`` produces an invalid pPr / tblPr /
# tcPr that Word refuses to open. Every insertion therefore uses
# ``insert_element_before`` with the full successor tag list.
PPR_AFTER_PBDR = [
    "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
    "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
    "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap",
    "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange",
]
TBLPR_AFTER_BORDERS = ["shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
                       "tblDescription", "tblPrChange"]
TBLPR_AFTER_MAR = ["tblLook", "tblCaption", "tblDescription", "tblPrChange"]
TCPR_AFTER_BORDERS = ["shd", "noWrap", "tcMar", "textDirection", "tcFitText",
                      "vAlign", "hideMark", "headers", "cellIns", "cellDel",
                      "cellMerge", "tcPrChange"]
TCPR_AFTER_SHD = ["noWrap", "tcMar", "textDirection", "tcFitText", "vAlign",
                  "hideMark", "headers", "cellIns", "cellDel", "cellMerge", "tcPrChange"]
TRPR_AFTER_HEADER = ["tblCellSpacing", "jc", "hidden", "ins", "del", "trPrChange"]


def _ordered(parent, tag: str, successors: list[str]):
    el = parent.find(qn("w:" + tag))
    if el is None:
        el = _el("w:" + tag)
        parent.insert_element_before(el, *["w:" + s for s in successors])
    return el


def _border(parent, edge: str, sz: int = 6, color: str = "1B365D", val: str = "single"):
    """Add a border edge to a paragraph's w:pPr (ordered insertion)."""
    borders = _ordered(parent, "pBdr", PPR_AFTER_PBDR)
    e = borders.find(qn("w:" + edge))
    if e is None:
        # pBdr is a plain lxml node here; exactly one edge ("bottom") is ever
        # added per holder, so a single append is already in schema order.
        e = _el("w:" + edge)
        borders.append(e)
    e.set(qn("w:val"), val)
    if val != "nil":
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "3")
        e.set(qn("w:color"), color)


def shade(cell, fill: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = _ordered(tcPr, "shd", TCPR_AFTER_SHD)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)


def cell_border_bottom(cell, sz=6, color="1B365D"):
    tcPr = cell._tc.get_or_add_tcPr()
    b = _ordered(tcPr, "tcBorders", TCPR_AFTER_BORDERS)
    bot = b.find(qn("w:bottom"))
    if bot is None:
        bot = _el("w:bottom")
        b.append(bot)
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), str(sz))
    bot.set(qn("w:color"), color)


def table_rules(table):
    tblPr = table._tbl.tblPr
    borders = _ordered(tblPr, "tblBorders", TBLPR_AFTER_BORDERS)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = borders.find(qn("w:" + edge))
        if e is None:
            e = _el("w:" + edge)
            borders.append(e)          # created in schema order
        if edge in ("top", "bottom"):
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), "8")
            e.set(qn("w:color"), "1B365D")
        else:
            e.set(qn("w:val"), "nil")
    mar = _ordered(tblPr, "tblCellMar", TBLPR_AFTER_MAR)
    for side, v in (("top", "55"), ("left", "85"), ("bottom", "55"), ("right", "85")):
        e = mar.find(qn("w:" + side))
        if e is None:
            e = _el("w:" + side)
            mar.append(e)
        e.set(qn("w:w"), v)
        e.set(qn("w:type"), "dxa")


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    h = _ordered(trPr, "tblHeader", TRPR_AFTER_HEADER)
    h.set(qn("w:val"), "true")


def field(paragraph, instr: str, placeholder: str = "1"):
    r = paragraph.add_run()
    b = _el("w:fldChar")
    b.set(qn("w:fldCharType"), "begin")
    r._r.append(b)
    r = paragraph.add_run()
    it = _el("w:instrText")
    it.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    it.text = instr
    r._r.append(it)
    r = paragraph.add_run()
    s = _el("w:fldChar")
    s.set(qn("w:fldCharType"), "separate")
    r._r.append(s)
    paragraph.add_run(placeholder)
    r = paragraph.add_run()
    e = _el("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    r._r.append(e)


RICH = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")


def rich(paragraph, text: str, *, size=9.5, color=BODY, font=SERIF):
    """Render a tiny inline markup: **bold**, *italic*, `mono`."""
    for tok in RICH.split(text):
        if not tok:
            continue
        bold = italic = mono = False
        if tok.startswith("**") and tok.endswith("**"):
            tok, bold = tok[2:-2], True
        elif tok.startswith("*") and tok.endswith("*"):
            tok, italic = tok[1:-1], True
        elif tok.startswith("`") and tok.endswith("`"):
            tok, mono = tok[1:-1], True
        r = paragraph.add_run(tok)
        r.font.name = MONO if mono else font
        r.font.size = Pt(size if not mono else size - 0.5)
        r.font.color.rgb = color
        r.bold = bold
        r.italic = italic
        if mono:
            rpr = r._r.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = _el("w:rFonts")
                rpr.append(rf)
            rf.set(qn("w:ascii"), MONO)
            rf.set(qn("w:hAnsi"), MONO)


# --------------------------------------------------------------------------- #
# document setup
# --------------------------------------------------------------------------- #
def setup_document() -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(20)
    sec.top_margin, sec.bottom_margin = Mm(18), Mm(16)
    sec.header_distance, sec.footer_distance = Mm(10), Mm(9)

    normal = doc.styles["Normal"]
    normal.font.name = SERIF
    normal.font.size = Pt(9.0)
    normal.font.color.rgb = BODY
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.08
    normal.paragraph_format.space_after = Pt(3.5)

    for name, sz, before, after in (("Heading 1", 12.5, 11, 5),
                                    ("Heading 2", 10.0, 8, 3),
                                    ("Heading 3", 9.2, 6, 2)):
        st = doc.styles[name]
        st.font.name = SANS
        st.font.size = Pt(sz)
        st.font.bold = True
        st.font.color.rgb = NAVY
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.keep_together = True
        st.paragraph_format.line_spacing = 1.05
    doc.styles["Heading 3"].font.italic = True

    # rule beneath every section heading
    pPr = doc.styles["Heading 1"]._element.get_or_add_pPr()
    _border(pPr, "bottom", sz=8, color="1B365D")

    cap = doc.styles["Caption"]
    cap.font.name = SANS
    cap.font.size = Pt(7.8)
    cap.font.color.rgb = GREY
    cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cap.paragraph_format.space_before = Pt(2)
    cap.paragraph_format.space_after = Pt(6)
    cap.paragraph_format.line_spacing = 1.06

    # running header
    hp = sec.header.paragraphs[0]
    hp.text = ""
    hp.paragraph_format.tab_stops.add_tab_stop(Mm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
    hp.paragraph_format.space_after = Pt(2)
    r = hp.add_run("ReMedFiLM  \u00b7  Complete Scientific Report  \u00b7  V8")
    r.font.name, r.font.size, r.font.color.rgb = SANS, Pt(7.3), GREY
    r = hp.add_run("\tRA-MedFiLM-BARR")
    r.font.name, r.font.size, r.font.color.rgb = SANS, Pt(7.3), GREY
    _border(hp._p.get_or_add_pPr(), "bottom", sz=4, color="C9D4E2")

    fp = sec.footer.paragraphs[0]
    fp.text = ""
    fp.paragraph_format.tab_stops.add_tab_stop(Mm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
    r = fp.add_run("Analysis-only reconstruction  \u00b7  no retraining  \u00b7  TEST1683 not opened")
    r.font.name, r.font.size, r.font.color.rgb = SANS, Pt(7.0), GREY
    r = fp.add_run("\tPage ")
    r.font.name, r.font.size, r.font.color.rgb = SANS, Pt(7.0), GREY
    field(fp, " PAGE ", "1")
    r = fp.add_run(" of ")
    r.font.name, r.font.size, r.font.color.rgb = SANS, Pt(7.0), GREY
    field(fp, " NUMPAGES ", "1")

    cp = doc.core_properties
    cp.title = "ReMedFiLM Complete Scientific Report V8"
    cp.subject = "Analysis-only reconstruction of the proposed ReMedFiLM FULL system"
    cp.keywords = "ReMedFiLM; RA-MedFiLM-BARR; FiLM; BARR; medical image segmentation"
    return doc


# --------------------------------------------------------------------------- #
# block renderers with global counters
# --------------------------------------------------------------------------- #
class Renderer:
    def __init__(self, doc: Document):
        self.doc = doc
        self.fig_no = 0
        self.tab_no = 0
        self.figures = []
        self.tables = []
        self.sections = []
        self.numeric_claims = []
        self.section_no = 0

    # -- text ------------------------------------------------------------- #
    def h1(self, text):
        self.section_no += 1
        self.sections.append({"number": self.section_no, "title": text})
        self.doc.add_heading(f"{self.section_no}.  {text}", level=1)

    def h2(self, text):
        self.doc.add_heading(text, level=2)

    def h3(self, text):
        self.doc.add_heading(text, level=3)

    def p(self, text, *, size=9.0, color=BODY, align=None, indent=None, space_after=None):
        par = self.doc.add_paragraph()
        if align is not None:
            par.alignment = align
        if indent is not None:
            par.paragraph_format.left_indent = Mm(indent)
        if space_after is not None:
            par.paragraph_format.space_after = Pt(space_after)
        rich(par, text, size=size, color=color)
        return par

    def bullets(self, items, size=8.8):
        for it in items:
            par = self.doc.add_paragraph(style="List Bullet")
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.left_indent = Mm(6)
            rich(par, it, size=size)

    def note(self, title, text, *, tone="navy"):
        col = {"navy": NAVY, "amber": AMBER, "red": RED}[tone]
        t = self.doc.add_table(rows=1, cols=1)
        t.autofit = False
        t.columns[0].width = Mm(TEXT_W)
        c = t.cell(0, 0)
        shade(c, LIGHT if tone == "navy" else "FBF6EA" if tone == "amber" else "FBF0F0")
        c.text = ""
        p0 = c.paragraphs[0]
        p0.paragraph_format.space_after = Pt(2)
        r = p0.add_run(title)
        r.font.name, r.font.size, r.font.bold, r.font.color.rgb = SANS, Pt(8.2), True, col
        p1 = c.add_paragraph()
        p1.paragraph_format.space_after = Pt(1)
        rich(p1, text, size=8.2)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def pagebreak(self):
        self.doc.add_page_break()

    # -- figures ---------------------------------------------------------- #
    def figure(self, fid: str, caption: str, *, width: float = WIDTH, source: str | None = None):
        self.fig_no += 1
        path = FIG_PATH[fid]
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before = Pt(4)
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.keep_with_next = True
        par.paragraph_format.keep_together = True
        par.add_run().add_picture(str(path), width=Mm(width))
        cap = self.doc.add_paragraph(style="Caption")
        cap.paragraph_format.keep_together = True
        r = cap.add_run(f"Figure {self.fig_no}.  ")
        r.bold = True
        r.font.color.rgb = NAVY
        rich(cap, caption, size=8.0, color=GREY, font=SANS)
        if source:
            r2 = cap.add_run("  [" + source + "]")
            r2.font.size = Pt(7.2)
            r2.font.color.rgb = GREY
        self.figures.append({
            "number": self.fig_no, "figure_id": fid,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(path), "width_mm": width,
            "caption": caption,
        })

    # -- tables ----------------------------------------------------------- #
    def table(self, caption: str, header: list[str], rows: list[list[str]], *,
              widths: list[float] | None = None, note: str | None = None,
              size: float = 8.0):
        self.tab_no += 1
        cp = self.doc.add_paragraph(style="Caption")
        cp.paragraph_format.space_after = Pt(3)
        cp.paragraph_format.keep_with_next = True
        r = cp.add_run(f"Table {self.tab_no}.  ")
        r.bold = True
        r.font.color.rgb = NAVY
        rich(cp, caption, size=8.0, color=GREY, font=SANS)

        t = self.doc.add_table(rows=1, cols=len(header))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        table_rules(t)
        if widths:
            for i, w in enumerate(widths):
                t.columns[i].width = Mm(w)
        hdr = t.rows[0]
        repeat_header(hdr)
        for i, h in enumerate(header):
            c = hdr.cells[i]
            c.text = ""
            shade(c, LIGHT)
            cell_border_bottom(c, sz=8)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            rr = p.add_run(h)
            rr.font.name, rr.font.size = SANS, Pt(size)
            rr.font.bold, rr.font.color.rgb = True, NAVY
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                c = cells[i]
                c.text = ""
                if ri % 2 == 1:
                    shade(c, LIGHTER)
                p = c.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.06
                rich(p, str(v), size=size, font=SERIF)
        if note:
            np_ = self.doc.add_paragraph()
            np_.paragraph_format.space_before = Pt(2)
            np_.paragraph_format.space_after = Pt(7)
            rich(np_, note, size=7.6, color=GREY)
        else:
            self.doc.add_paragraph().paragraph_format.space_after = Pt(3)
        self.tables.append({"number": self.tab_no, "caption": caption,
                            "header": header, "n_rows": len(rows)})

    def claim(self, mid: str, formatted: str):
        self.numeric_claims.append({"metric_id": mid, "value": M(mid),
                                    "printed": formatted})


# --------------------------------------------------------------------------- #
# content
# --------------------------------------------------------------------------- #
def build(doc: Document) -> Renderer:
    R = Renderer(doc)
    cr = REG["canonical_result"]
    route = REG["routing_val808"]

    # ---------------- front matter ---------------- #
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(0)
    sp.paragraph_format.space_before = Pt(28)
    r = sp.add_run("ReMedFiLM")
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = SANS, Pt(26), True, NAVY

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)
    r = sp.add_run("Complete Scientific Report")
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = SANS, Pt(17), True, TEAL

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(14)
    r = sp.add_run("Version 8  \u00b7  analysis-only reconstruction from frozen artifacts")
    r.font.name, r.font.size, r.font.color.rgb = SANS, Pt(10), GREY

    _border(sp._p.get_or_add_pPr(), "bottom", sz=12, color="1B365D")

    R.p("**Proposed model.**  ReMedFiLM FULL, implemented as `RA-MedFiLM-BARR`, "
        "is the four-component system **G + R_psi + B_phi + S_omega**. "
        "**GlobalMedFiLM is the `G` backbone and a legitimate ablation baseline "
        "only** \u2014 it is not the proposed model and must never be labelled "
        "ReMedFiLM FULL. This distinction is enforced throughout V8.", size=10.0,
        space_after=8)

    R.note("Abstract",
           f"On the held-out VAL808 split (n = {cr['n']}, seed {cr['seed']}), the proposed "
           f"ReMedFiLM FULL attains a domain-equal-weight macro Dice of "
           f"**{f4(cr['full_macro_dice'], 6)}**, against **{f4(cr['global_macro_dice'], 6)}** "
           f"for its GlobalMedFiLM backbone; the paired gain is "
           f"**+{f4(cr['paired_delta_dice'], 6)}** (95% bootstrap CI "
           f"{f4(cr['paired_delta_ci_low'], 6)}\u2013{f4(cr['paired_delta_ci_high'], 6)}, "
           f"10,000 domain-stratified image resamples). The gain is concentrated in KUB "
           f"radiography (+{f4(M('INT_KUB_PAIRED_DELTA_DICE'), 6)}). On 884 retrospective "
           f"external images the system is directionally consistent but the margin is small, "
           f"and on 20 KUB stone images both systems perform poorly "
           f"(FULL {f4(M('EXT_STONES_FULL_DICE'))} vs G {f4(M('EXT_STONES_G_DICE'))}). "
           "A 13-arm ablation shows that learned benefit routing dominates the gain, while "
           "the incremental contribution of the post-safety gate is **not established** "
           "(A8 \u2212 A7 CI includes zero). V8 also adjudicates a legacy headline value, "
           "0.837862, and rejects it as a reporting inconsistency rather than a second "
           "experimental configuration. All V8 numbers trace to a single source-linked "
           "registry of 291 metric records. No model was retrained, no new inference was "
           "run, no checkpoint was modified, and the protected TEST1683 inputs were not opened.")

    R.note("Status of evidence",
           "**Established:** paired VAL808 preservation result; frozen state-machine counts; "
           "external descriptive comparison; historical 13-arm ablation; staged objectives. "
           "**Not established:** C1 (learned vs identity FiLM), C2 (causal safety-gate "
           "attribution), C3 (matched multi-seed baseline matrix), any prospective TEST1683 "
           "evaluation, and patient-level independence of the BrEaST external cohort. "
           "No p-values are added in V8 beyond the pre-registered bootstrap intervals.",
           tone="amber")

    R.h2("Contents")
    toc = doc.add_paragraph()
    field(toc, ' TOC \\o "1-2" \\h \\z \\u ',
          "Table of contents is generated on open / export.")
    R.p("*This report is deliberately undated: the build host clock is not synchronised "
        "(NTP leap indicator 3), so absolute timestamps would carry an unquantified offset. "
        "Provenance is established by SHA-256 digests in Section 11 instead.*",
        size=8.2, color=GREY)
    R.pagebreak()

    # ---------------- 1 ---------------- #
    R.h1(SECTION_TITLES[0])
    R.p("Medical segmentation models are usually evaluated as single monolithic networks. "
        "ReMedFiLM asks a different question: given one task-conditioned global segmenter, "
        "can a **conditional** system decide *per image* whether a regional refinement should "
        "be executed, and whether its result is safe to keep? The proposed answer is a "
        "four-component, sequentially trained system whose inference path is a verified "
        "state machine rather than a single joint network.")
    R.h2("1.1  Canonical identity")
    R.p("**ReMedFiLM FULL = RA-MedFiLM-BARR = G + R_psi + B_phi + S_omega.** "
        "The assembly wrapper itself has zero trainable parameters and defines no loss: "
        "it is an inference-time composition of four independently trained modules. "
        "Conflating the assembly with any one component \u2014 most often with the "
        "GlobalMedFiLM backbone \u2014 is the principal scientific error corrected in V8.")

    comp_rows = []
    for key, label, cls in (
        ("G", "G \u2014 task-conditioned backbone", "GlobalMedFiLM"),
        ("R_psi", "R_psi \u2014 regional refiner", "BARRRegionalRefinerV1"),
        ("B_phi", "B_phi \u2014 benefit router", "BARRBenefitRouterV1"),
        ("S_omega", "S_omega \u2014 post-safety gate", "BARRPostSafetyV1"),
    ):
        params = {"G": "3,523,001", "R_psi": "1,276,401",
                  "B_phi": "36,801", "S_omega": "1,217"}[key]
        comp_rows.append([label, cls, params])
    R.table("Canonical component chain of the proposed model (verified by read-only "
            "checkpoint state-dict loading).",
            ["Component", "Implementation class", "Parameters"],
            comp_rows + [["**ReMedFiLM FULL (assembly)**",
                          "**RAMedFiLMBARR**", "**4,837,420**"]],
            widths=[62, 70, 38],
            note="Total is the sum of the four component counts; the wrapper adds no "
                 "parameters. FiLM + task-embedding parameters inside G are 90,768 "
                 "(2.58% of G). Freezing a module does not reduce total parameter count.")

    R.h2("1.2  Contributions")
    R.bullets([
        "**A task-conditioned global backbone.** `GlobalMedFiLM` uses one shared "
        "encoder\u2013decoder for four imaging domains; task identity enters only through a "
        "32-D embedding and five FiLM modulation sites, `F_hat = (1 + gamma(t)) F + beta(t)`.",
        "**A four-state conditional inference machine.** Benefit routing and a post-safety "
        "gate decide per image whether to execute an offline regional refinement, with a "
        "deterministic global fallback on both skip and reject paths.",
        "**A strictly staged, independently supervised training protocol.** G, R_psi, "
        "B_phi and S_omega have four distinct objectives and are trained sequentially "
        "against frozen upstream outputs; there is no joint end-to-end optimisation.",
        "**A source-linked evidence base.** 291 metric records with run IDs, seeds, "
        "checkpoint digests, metric definitions, aggregation rules and SHA-256 source "
        "digests, plus a 33-figure evidence map and a 20-arrow code-verification manifest.",
        "**An explicit negative-results record.** Unresolved comparisons, a non-established "
        "safety contribution, a clinically important external false-positive pattern, and "
        "a rejected legacy headline value are all reported rather than suppressed.",
    ])

    R.h2("1.3  Headline result and its provenance")
    R.p(f"The result reported for the proposed system is the *paired* comparison on VAL808: "
        f"FULL {f4(cr['full_macro_dice'], 6)} versus backbone {f4(cr['global_macro_dice'], 6)}, "
        f"a difference of +{f4(cr['paired_delta_dice'], 6)} Dice "
        f"(+{f4(cr['paired_delta_dice'] * 100, 4)} percentage points). "
        "Section 11 adjudicates the three values that circulated in earlier report versions "
        "and explains why only one of them is a measurement of the proposed model.")
    R.claim("INT_MACRO_DOMAIN_EQUAL_WEIGHT_FULL_DICE", f4(cr["full_macro_dice"], 6))
    R.claim("INT_MACRO_DOMAIN_EQUAL_WEIGHT_G_DICE", f4(cr["global_macro_dice"], 6))
    R.claim("INT_MACRO_DELTA_POINT", f4(cr["paired_delta_dice"], 6))
    R.figure("V8_F03_result_reconciliation",
             "V8 adjudication of the three VAL808 macro-Dice values. Left: the canonical "
             "FULL result (teal), its GlobalMedFiLM comparator (blue), and the legacy "
             "0.837862 (rejected). Right: the genuine three-seed values re-aggregated from "
             "the frozen per-sample NPZ archive, with seed 42 matching the saved-mask "
             "re-score to approximately 6\u00d710\u207b\u2077. The legacy value is the mean of "
             "three numbers hard-coded into the V5/V6/V7 generators, not a measurement.",
             width=WIDTH, source="V8 registry; frozen NPZ; V7 generator")

    # ---------------- 2 ---------------- #
    R.h1(SECTION_TITLES[1])
    R.h2("2.1  Verified architecture")
    R.p("Every arrow in the V8 methodology figure was checked against source code. "
        f"The verification manifest records **{ARROWS['verified_arrow_count']} supported "
        f"arrows** and **{ARROWS['removed_or_corrected_count']} arrows removed or "
        "corrected** relative to the V5\u2013V7 diagram. The most consequential corrections "
        "are: B_phi is *pre*-refinement and never sees the ROI crop or a global feature "
        "tensor; S_omega is *post*-candidate-composition; R_psi is an offline out-of-fold "
        "producer and is not invoked online; fusion is deterministic replacement inside the "
        "ROI with no alpha blending; and there are **two** distinct skip states rather than one.")
    R.figure("ReMedFiLM_Methodology_V8",
             "Code-verified three-panel methodology. Panel A: four multi-domain inputs and "
             "three distinct task representations. Panel B: the full inference state machine "
             "of `RAMedFiLMBARR.forward_inference`, showing G \u2192 action/ROI \u2192 B_phi "
             "\u2192 utility test \u2192 offline OOF refined crop \u2192 deterministic fusion "
             "\u2192 S_omega \u2192 accept/reject, with both skip states. Panel C: the six-step "
             "sequential training dependency, explicitly not joint end-to-end training. "
             "Blue denotes GlobalMedFiLM, teal denotes the proposed ReMedFiLM FULL system.",
             width=168.0, source="v8_figure_methodology.py; 20 verified arrows")

    R.h2("2.2  G: task-conditioned GlobalMedFiLM (backbone only)")
    R.p("`GlobalMedFiLM` is a single shared encoder\u2013decoder with channel widths "
        "(24, 48, 96, 192, 256) and five FiLM sites at `bridge`, `decoder4`, `decoder3`, "
        "`decoder2` and `decoder1`. A 32-D learned task embedding is mapped through a "
        "64-D hidden layer to `gamma = tanh(gamma_raw)` and `beta = tanh(beta_raw)` at each "
        "site; the output projections are zero-initialised so every site begins as an exact "
        "identity transform. The source file states explicitly that the module contains no "
        "ROI proposal, localiser, crop branch, router, gain label or safety head. "
        "**It is the `G` component and a legitimate ablation baseline, not the proposed system.**")

    R.h2("2.3  R_psi, B_phi and S_omega")
    R.p("`BARRRegionalRefinerV1` (R_psi) is a plain 4-channel CNN over ROI crops; it has no "
        "FiLM, attention or residual-correction head, and emits a **refined crop probability "
        "map**, not an additive `delta P`. `BARRBenefitRouterV1` (B_phi) consumes a frozen, "
        "ground-truth-free 202-D numeric feature vector plus its own 16-D task embedding "
        "(218 inputs) and regresses `delta_dice` through "
        "`Linear(218,128) \u2192 LayerNorm \u2192 SiLU \u2192 Dropout \u2192 Linear(128,64) "
        "\u2192 \u2026 \u2192 Linear(64,1)`. `BARRPostSafetyV1` (S_omega) consumes 16 frozen "
        "post-candidate numeric features concatenated with a 4-D one-hot task vector (20 "
        "inputs) through `Linear(20,32) \u2192 SiLU \u2192 Linear(32,16) \u2192 SiLU "
        "\u2192 Linear(16,1)`. The three modules therefore use **three different task "
        "representations**: 32-D embedding, 16-D embedding, and 4-D one-hot.")

    R.h2("2.4  Verified inference state machine")
    R.p("`forward_inference` executes G exactly once, derives action availability and the "
        "ROI window from `p_global >= 0.30`, and then follows one of four states. The router "
        "utility is `U = delta_hat_final \u2212 (1/4)(1051648/10270749)` with "
        "`tau_C8 = -0.024358327623641256`; `U < tau_C8` returns SKIP_GLOBAL. On the execute "
        "path a supplied out-of-fold `oof_refined_crop_prob` is fused by replacing `p_global` "
        "inside the (1.5\u00d7 expanded) ROI while retaining `p_global` outside it. S_omega "
        "then scores post-candidate features and accepts when its sigmoid is `>= 0.50`; "
        "rejection restores `p_global`. The final binary mask uses the separate "
        "`SEGMENTATION_OUTPUT_THRESHOLD = 0.50`.")
    R.note("Three distinct 0.50 / 0.30 thresholds \u2014 not interchangeable",
           "`ROI_PROPOSAL_THRESHOLD = 0.30` governs bbox/action availability; "
           "`SEGMENTATION_OUTPUT_THRESHOLD = 0.50` binarises the final mask and all reported "
           "Dice; `SOMEGA_ACCEPT_THRESHOLD = 0.50` governs the post-safety accept decision. "
           "Only the first is a proposal threshold.", tone="navy")
    R.figure("V8_F02_four_state_flow",
             "The four canonical VAL808 states of `RAMedFiLMBARR.forward_inference`. "
             "FORCED_SKIP occurs when no action is available; SKIP_GLOBAL occurs when the "
             "router utility falls below tau_C8. Executed cases split into accept and reject "
             "according to S_omega. Counts are from the frozen Phase 27 prediction table.",
             width=WIDTH, source="phase27_val808_predictions.csv")
    R.figure("A02_component_presence_matrix",
             "Component-presence matrix. Only the FULL assembly instantiates all four "
             "components; GlobalMedFiLM alone instantiates G only. This is the identity "
             "check that prevents the backbone from being reported as the proposed model.",
             width=146.0, source="figure_registry.json / A02")

    R.h2("2.5  Staged training \u2014 sequential, not joint")
    R.p("The six-step dependency is: train G \u2192 generate global predictions/ROIs \u2192 "
        "train R_psi \u2192 create paired gain labels \u2192 train B_phi \u2192 train S_omega. "
        "Inference uses frozen modules and frozen out-of-fold caches. The wrapper defines no "
        "trainable parameters and no unified objective, so **no joint end-to-end "
        "backpropagation occurs**; claims of end-to-end training in earlier versions are "
        "unsupported.")
    R.table("Verified per-stage objectives. Each stage is supervised independently; "
            "no gradient passes between stages.",
            ["Stage", "Module", "Objective", "Target"],
            [
                ["1", "G", "BCEWithLogits + soft Dice (historical `train_loss` / `val_loss`)", "binary mask"],
                ["2", "R_psi", "0.5 \u00d7 BCEWithLogits + 0.5 \u00d7 soft Dice", "ROI-crop mask"],
                ["3", "B_phi", "`nn.HuberLoss(delta=0.05, reduction='mean')`", "`delta_dice`"],
                ["4", "S_omega", "`BCEWithLogitsLoss(reduction='mean')`", "binary `safety_target`"],
            ],
            widths=[14, 22, 88, 46],
            note="Phase 25C gain labels contain `delta_dice`, `gain_category`, `global_dice` "
                 "and `candidate_refined_dice`. S_omega targets `sign(delta_dice)` "
                 "\u2014 it scores refinement benefit, not lesion presence or clinical "
                 "reliability.")
    R.figure("ReMedFiLM_Methodology_Manuscript",
             "Portrait print variant of the **same** verified state machine shown in Figure 2, "
             "reformatted for single-column manuscript reproduction. It is not a second "
             "architecture and introduces no additional pathways or objectives.",
             width=104.0, source="v8_figure_methodology.py / manuscript variant")

    # ---------------- 3 ---------------- #
    R.h1(SECTION_TITLES[2])
    R.h2("3.1  Datasets and licensing")
    R.table("Source datasets. Dataset licences are separate from the repository code, "
            "which currently has no licence file.",
            ["Dataset", "Modality / target", "Licence / use condition", "Role"],
            [
                ["ISIC 2018", "Dermoscopy / skin lesion", "Task 1 data: CC0", "internal"],
                ["BUSI-WHU", "Breast ultrasound / lesion", "CC BY 4.0, attribution required", "internal"],
                ["Kvasir-SEG", "Endoscopy / GI polyp", "Research/educational; commercial use needs written permission", "internal + CVC external comparator context"],
                ["KUB-StoneX", "KUB radiography / stone", "CC BY 4.0, attribution required", "internal"],
            ],
            widths=[27, 45, 62, 36], size=7.8)
    R.p("**KUB unit-of-analysis caveat.** The KUB manifest contains full-field radiographs "
        "and ROI instance patches; these are different units of analysis and must not be "
        "pooled as if interchangeable. The BUSI-WHU workbook distributed with the dataset "
        "is deliberately excluded from all published artifacts.")

    R.h2("3.2  Split accounting and protected data")
    R.p(f"Internal data are partitioned into TRAIN (n = {REG['populations']['TRAIN']:,}), "
        f"VAL808 (n = {REG['populations']['VAL808']}) and the protected TEST1683 cohort. "
        f"Router development used ROUTER_DEV "
        f"({REG['populations']['ROUTER_DEVELOPMENT_4957']:,}) plus a locked ROUTER_HOLDOUT "
        f"({REG['populations']['ROUTER_HOLDOUT_875']:,}), which together reconstitute TRAIN. "
        "VAL808 domain counts are ISIC 357, BUSI 84, Kvasir 87 and KUB 280. "
        "**TEST1683 was never opened during V8 reconstruction**, and V8 reports no "
        "prospective test result.")
    R.table("Population accounting used in V8. Values are counts of images unless stated.",
            ["Population", "n", "Status in V8"],
            [
                ["TRAIN", f"{REG['populations']['TRAIN']:,}", "component training; frozen"],
                ["VAL808", "808", "canonical paired evaluation, seed 42"],
                ["ROUTER_DEV + ROUTER_HOLDOUT", "4,957 + 875", "13-arm ablation population"],
                ["TEST1683", "1,683", "**PROTECTED \u2014 not opened**"],
                ["EXTERNAL884", "612 + 252 + 20", "retrospective, no training"],
            ],
            widths=[58, 40, 72])
    R.figure("D01_domain_and_split_composition",
             "Domain and split composition of the internal four-domain cohort.",
             width=WIDTH, source="frozen manifests / D01")
    R.figure("D03_kub_unit_of_analysis",
             "KUB unit-of-analysis: full-field radiographs versus ROI instance patches.",
             width=138.0, source="frozen manifests / D03")
    R.figure("STAT04_population_accounting",
             "Population accounting across TRAIN, VAL808, router development/holdout and "
             "the protected TEST1683 cohort.",
             width=150.0, source="registry populations / STAT04")

    R.h2("3.3  Metric definitions and aggregation")
    R.p("Dice is computed on the binary mask produced at the 0.50 output threshold. "
        "The headline 'macro' value is the **equal-weight mean of the four per-domain "
        "per-image Dice means**, not a pooled image-level mean; this gives each domain "
        "equal weight despite the unequal domain sizes. The paired difference is computed "
        "per image and then averaged. Its 95% interval is a percentile bootstrap with "
        "10,000 domain-stratified image resamples, seed 20261027. V8 adds no new p-values "
        "and reports no interval that was not present in the frozen evidence.")
    R.note("Out-of-fold boundary (a genuine limitation, deliberately not repaired)",
           "In the full pipeline, refiner, router and safety stages use out-of-fold labels "
           "(OOF = TRUE) while the backbone is in-sample (OOF = FALSE). Consequently the "
           "backbone-conditioned delta-Q and harm rates are **optimistic**. V8 records this "
           "asymmetry rather than silently correcting it.", tone="amber")

    # ---------------- 4 ---------------- #
    R.h1(SECTION_TITLES[3])
    R.h2("4.1  Canonical paired result")
    dom = [("ISIC", "ISIC", 357), ("BUSI", "BUSI", 84),
           ("Kvasir", "KVASIR", 87), ("KUB", "KUB", 280)]
    rows = []
    for label, key, n in dom:
        rows.append([label, str(n), f4(M(f"INT_{key}_G_DICE")),
                     f4(M(f"INT_{key}_FULL_DICE")),
                     f"+{f4(M(f'INT_{key}_PAIRED_DELTA_DICE'))}"])
    rows.append(["**Macro (equal domain weight)**", "**808**",
                 f"**{f4(M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_G_DICE'))}**",
                 f"**{f4(M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_FULL_DICE'))}**",
                 f"**+{f4(M('INT_MACRO_DELTA_POINT'))}**"])
    R.table("VAL808 internal results. ReMedFiLM FULL versus its GlobalMedFiLM backbone, "
            "seed 42, identical images and identical output threshold.",
            ["Domain", "n", "G Dice", "FULL Dice", "Paired \u0394"],
            rows, widths=[58, 18, 32, 32, 30],
            note="95% CI for the macro paired \u0394: "
                 f"[{f4(cr['paired_delta_ci_low'], 6)}, {f4(cr['paired_delta_ci_high'], 6)}]. "
                 "Macro = equal-weight mean of the four domain means. "
                 "All values re-scored from saved masks; no new inference.")
    R.p(f"The overall gain is small and highly domain-dependent: KUB contributes "
        f"+{f4(M('INT_KUB_PAIRED_DELTA_DICE'))} Dice, while BUSI contributes only "
        f"+{f4(M('INT_BUSI_PAIRED_DELTA_DICE'))}. Across the 808 images, "
        f"{M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_BENEFICIAL')} improve, "
        f"{M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_UNCHANGED')} are unchanged and "
        f"{M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_HARMFUL')} are harmed relative to the backbone. "
        "The 542 unchanged cases are overwhelmingly the SKIP_GLOBAL branch, whose saved "
        "FULL mask is byte-identical to the backbone mask.")
    R.figure("I1_domain_metric_comparison",
             "Per-domain comparison of GlobalMedFiLM and ReMedFiLM FULL across Dice, IoU, "
             "precision and recall on VAL808.",
             width=WIDTH, source="V8 registry / I1")
    R.figure("I2_paired_delta_forest",
             "Paired per-image \u0394 Dice by domain with the macro estimate and its "
             "domain-stratified bootstrap interval.",
             width=150.0, source="V8 registry / I2")
    R.figure("STAT02_bootstrap_distribution",
             "Bootstrap distribution of the paired macro \u0394 Dice (10,000 stratified "
             "resamples, seed 20261027). The percentile interval excludes zero.",
             width=146.0, source="REMEDFILM_PAIRED_DELTA.json / STAT02")

    R.h2("4.2  Six-model context \u2014 historical descriptive comparison")
    R.table("VAL808 context of the frozen six-model comparison. These are historical "
            "descriptive results, **not** a matched controlled experiment.",
            ["Model", "Macro Dice"],
            [
                ["GlobalMedFiLM (G, backbone / baseline)", f4(M("BASE_GLOBAL_MEDFILM_MACRO_DICE"))],
                ["DeepLabV3+", f4(M("BASE_DEEPLABV3PLUS_MACRO_DICE"))],
                ["Transformer / MiT-style U-Net", f4(M("BASE_TRANSFORMER_MIT_UNET_MACRO_DICE"))],
                ["U-Net++", f4(M("BASE_UNETPP_MACRO_DICE"))],
                ["Attention U-Net", f4(M("BASE_ATTENTION_UNET_MACRO_DICE"))],
                ["U-Net", f4(M("BASE_UNET_MACRO_DICE"))],
                ["**ReMedFiLM FULL (proposed)**",
                 f"**{f4(M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_FULL_DICE'))}**"],
            ],
            widths=[118, 52],
            note="The FULL row comes from the canonical re-score, not from this legacy "
                 "table. The two GlobalMedFiLM entries differ by ~3\u00d710\u207b\u2077 "
                 "because they are distinct source artifacts; V8 does not silently merge "
                 "them. No matched multi-seed baseline matrix (C3) has been established.")

    # ---------------- 5 ---------------- #
    R.h1(SECTION_TITLES[4])
    R.p("Training histories are reported per module, not as a single curve. V8 reads the "
        "frozen component training-history table and selects one genuine run ID per panel; "
        "no curve is spliced from different runs. The G backbone history covers 81 recorded "
        "epochs of `val_macro_dice` under run "
        "`phase21_global_medfilm_fourdomain_seed42_clean_v3`.")
    t = [x for x in REG["metrics"] if x["metric_id"].startswith("TRAIN_")]
    R.p(f"G validation macro Dice rises from {f4(t[0]['value'])} at epoch 1 to "
        f"{f4(t[-1]['value'])} at epoch 81, with a maximum of "
        f"{f4(max(x['value'] for x in t))}. That maximum "
        f"({f4(max(x['value'] for x in t))}) agrees with the frozen backbone comparator "
        f"{f4(M('BASE_GLOBAL_MEDFILM_MACRO_DICE'))} to within 3\u00d710\u207b\u2077, "
        "confirming that the history and the comparator refer to the same trained backbone.")
    R.figure("V8_F04_training_dashboard",
             "Four independent objective histories \u2014 G, R_psi, B_phi and S_omega. "
             "Each panel uses a single genuine run ID for both train and validation curves. "
             "The B_phi Huber loss shows a large epoch-1 transient; panels are individually "
             "scaled. These are four separate training procedures, not one joint run.",
             width=WIDTH, source="REMEDFILM_COMPONENT_TRAINING_HISTORY.csv")
    R.figure("T2_val_dice_across_epochs",
             "GlobalMedFiLM validation macro Dice across the recorded training epochs.",
             width=142.0, source="training history / T2")
    R.figure("T4_per_domain_learning_curves",
             "Per-domain learning curves for the shared backbone, showing the unequal "
             "convergence of the four domains.",
             width=142.0, source="training history / T4")
    R.note("What the histories do and do not establish",
           "They document that four modules were trained with distinct objectives and "
           "that the backbone converged. They are **not** three independent end-to-end "
           "training replicates: the three-seed downstream runs share one pre-trained "
           "backbone. No history in V8 was regenerated by retraining.", tone="amber")

    # ---------------- 6 ---------------- #
    R.pagebreak()
    R.h1(SECTION_TITLES[5])
    R.p("The following galleries show real saved predictions, ground truth and the two "
        "system outputs for representative VAL808 cases. All tiles come from the frozen "
        "Phase 27 / Phase 29 validation caches and are rendered at the 0.50 segmentation "
        "output threshold. **No new inference was run to produce any V8 image.** "
        "Tiles are illustrative cases, not a random or pre-registered sample, and must not "
        "be read as a quantitative estimate.")
    for fid, label in (
        ("SEG_ISIC_global_vs_full", "ISIC 2018 dermoscopy"),
        ("SEG_BUSI_global_vs_full", "BUSI-WHU breast ultrasound"),
        ("SEG_KVASIR_global_vs_full", "Kvasir-SEG endoscopy"),
        ("SEG_KUB_global_vs_full", "KUB radiography"),
    ):
        R.figure(fid,
                 f"Real segmentation examples \u2014 {label}. Each row shows the input, "
                 "ground truth, the GlobalMedFiLM backbone output and the ReMedFiLM FULL "
                 "output with the ROI and the routing/safety decision annotated. "
                 "Differences are typically local boundary adjustments rather than whole-"
                 "mask changes, consistent with the small paired \u0394 Dice.",
                 width=168.0, source="frozen Phase 27 / 29 validation caches")
    R.figure("SEG_failure_cases",
             "Representative failure cases retained as negative evidence. These include "
             "harmful refinements and false-positive foreground on stone-free radiographs; "
             "they are shown because the aggregate Dice gain does not imply uniform "
             "per-image benefit.",
             width=168.0, source="frozen validation / external caches")

    # ---------------- 7 ---------------- #
    R.h1(SECTION_TITLES[6])
    R.p("Subgroup analyses are descriptive stratifications of the frozen predictions. "
        "They are not powered comparisons, no multiplicity correction is applied, and V8 "
        "reports no subgroup p-values. The KUB radiography domain is the only internal "
        f"domain with a material paired gain (+{f4(M('INT_KUB_PAIRED_DELTA_DICE'))}), so "
        "its stone morphology and size strata receive the most attention.")
    R.figure("SG1_kub_stone_subgroups",
             "KUB stone morphological subclasses. Performance varies across subclasses; "
             "the strata are descriptive and the subgroup sample sizes are small.",
             width=142.0, source="c1_external_stress_stones_subgroups.csv / SG1")
    R.figure("SG2_kub_size_stratification",
             "KUB stone size stratification. Small objects remain the dominant failure mode, "
             "consistent with the poor external Stones-Where-Are-You result in Section 8.",
             width=142.0, source="subgroup evidence / SG2")
    R.note("Excluded legacy subgroup table",
           "`tables/subgroup_performance_summary.csv` is a V3-era artifact containing the "
           "superseded 0.8379 macro / +0.28 pp figures. It is excluded from every V8 table "
           "and figure; the exclusion is recorded in the results registry.", tone="red")

    # ---------------- 8 ---------------- #
    R.h1(SECTION_TITLES[7])
    R.p(f"The external retrospective cohort comprises "
        f"{REG['populations']['EXTERNAL884']['CVC-ClinicDB']} CVC-ClinicDB, "
        f"{REG['populations']['EXTERNAL884']['BrEaST-Lesions-USG']} BrEaST-Lesions-USG and "
        f"{REG['populations']['EXTERNAL884']['Stones_where_are_you']} "
        "Stones-Where-Are-You images (884 total). No external image was used for training, "
        "threshold selection or model selection; these are held-out retrospective "
        "descriptive comparisons. Patient-level independence of the BrEaST cohort cannot "
        "be verified from the available artifacts and is disclosed as a limitation.")
    ext_rows = []
    for label, key, n in (("CVC-ClinicDB", "CVC", 612),
                          ("BrEaST-Lesions-USG", "BREAST", 252),
                          ("Stones-Where-Are-You", "STONES", 20)):
        ext_rows.append([
            label, str(n),
            f4(M(f"EXT_{key}_G_DICE")), f4(M(f"EXT_{key}_FULL_DICE")),
            f4(M(f"EXT_{key}_G_HD95_PX"), 2), f4(M(f"EXT_{key}_FULL_HD95_PX"), 2),
        ])
    R.table("External retrospective results: Dice and HD95 for the GlobalMedFiLM backbone "
            "and the proposed ReMedFiLM FULL system. Direction is consistent across cohorts; "
            "margins are small.",
            ["Cohort", "n", "G Dice", "FULL Dice", "G HD95 px", "FULL HD95 px"],
            ext_rows, widths=[45, 14, 27, 27, 29, 28],
            note="HD95, ASSD, recall are defined on only n = 6 of the 20 Stones images; "
                 "Dice/IoU/precision use n = 20. Denominators are stated per metric in "
                 "REMEDFILM_V8_EXTERNAL_EVALUATION.csv and in V8_F05.")
    R.figure("V8_F05_external_metric_coverage",
             "External metric coverage. Six metrics \u00d7 two systems \u00d7 three cohorts, "
             "with cells annotated by the true denominator. Partial-coverage cells "
             "(n = 6/20 for Stones HD95, ASSD and recall) are visually distinguished "
             "rather than presented as full-cohort estimates.",
             width=WIDTH, source="REMEDFILM_V8_EXTERNAL_EVALUATION.csv")
    R.figure("EXT01_external_dice",
             "External Dice by cohort and system, with the stone-free subgroup shown "
             "separately.", width=152.0, source="frozen external metrics / EXT01")
    R.figure("EXT02_external_delta",
             "Paired external \u0394 Dice distribution by cohort. The IQR sits exactly on "
             "zero for the stone-free subgroup, so most external images are unchanged.",
             width=138.0, source="frozen external metrics / EXT02")
    R.figure("EXT03_stonefree_false_positive",
             "Negative result: all 14 stone-free external images receive false-positive "
             "foreground predictions from both systems. S_omega scores refinement benefit "
             "(sign of \u0394 Dice), not lesion presence, and therefore cannot suppress "
             "a false positive that is already present in the backbone output.",
             width=138.0, source="c1_external_stress artifacts / EXT03")
    R.note("Negative result preserved",
           "**14 / 14** stone-free images receive false-positive foreground predictions. "
           "For the 9 stone-free images with a negative change, no harmful case may be "
           "invented. The external verdict is 'directionally consistent, 0 failures of the "
           "preservation property', **not** 'clinically safe'. No diagnosis is inferred and "
           "no clinical deployment claim is made.", tone="red")

    # ---------------- 9 ---------------- #
    R.h1(SECTION_TITLES[8])
    R.p("Component progression is reported on VAL808 for the frozen state machine, while "
        "the 13-arm ablation is reported on ROUTER_DEVELOPMENT (n = 4,957). These are "
        "**different populations** and their fractions must not be compared as if matched. "
        "The ablation is a policy comparison over frozen arm outputs, not a causal "
        "retraining ablation; `n_executed` is a property of the policy, not of the dataset.")
    R.table("Frozen component progression. Stage 0 is the backbone; Stage 4 is the "
            "canonical VAL808 state machine.",
            ["Stage", "Population", "Routed", "Accepted", "Mean \u0394", "Harmful", "GMACs"],
            [
                ["0 \u2014 G only", "VAL808", "0.0000", "0.0000", "0.0000", "0.0000",
                 f4(M("ABL_STAGE_0_GMACS"), 3)],
                ["1 \u2014 always refine", "ROUTER_DEV", "1.0000", "1.0000",
                 f4(M("ABL_STAGE_1_MEAN_DELTA_DICE")),
                 f4(M("ABL_STAGE_1_HARMFUL_SHARE")), f4(M("ABL_STAGE_1_GMACS"), 3)],
                ["2 \u2014 + ROI policy", "ROUTER_DEV", f4(M("ABL_STAGE_2_ROUTED_FRACTION")),
                 f4(M("ABL_STAGE_2_ACCEPTED_FRACTION")),
                 f4(M("ABL_STAGE_2_MEAN_DELTA_DICE")),
                 f4(M("ABL_STAGE_2_HARMFUL_SHARE")), f4(M("ABL_STAGE_2_GMACS"), 3)],
                ["3 \u2014 + safety", "ROUTER_DEV", f4(M("ABL_STAGE_3_ROUTED_FRACTION")),
                 f4(M("ABL_STAGE_3_ACCEPTED_FRACTION")),
                 f4(M("ABL_STAGE_3_MEAN_DELTA_DICE")),
                 f4(M("ABL_STAGE_3_HARMFUL_SHARE")), f4(M("ABL_STAGE_3_GMACS"), 3)],
                ["**4 \u2014 FULL / VAL808**", "**VAL808**",
                 f"**{f4(M('ABL_STAGE_4_ROUTED_FRACTION'))}**",
                 f"**{f4(M('ABL_STAGE_4_ACCEPTED_FRACTION'))}**",
                 f"**{f4(M('ABL_STAGE_4_MEAN_DELTA_DICE'))}**",
                 f"**{f4(M('ABL_STAGE_4_HARMFUL_SHARE'))}**",
                 f"**{f4(M('ABL_STAGE_4_GMACS'), 3)}**"],
            ],
            widths=[36, 26, 21, 21, 21, 21, 24], size=7.6,
            note="Stages 1\u20133 'Mean \u0394' and 'Harmful' are percentage-point scale "
                 "values in the frozen progression table; Stage 4 values reproduce the "
                 "canonical +0.2210 pp and 0.1200 harm share. The legacy "
                 "PROGRESSION_AND_PROPAGATION_EVIDENCE.csv records conflicting Stage 4 "
                 "values and is excluded.")
    R.figure("PROG01_stage_compute_and_harm",
             "Component progression: conditional compute and harm share across stages. "
             "Routing removes most of the harm introduced by unconditional refinement.",
             width=152.0, source="REMEDFILM_ABLATION_AND_PROGRESSION.csv / PROG01")

    arms = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
            "R1", "R2", "R3", "F1"]
    R.p("The 13 arms are: A0 (never refine), A1 (always refine), A2 (fixed ROI policy), "
        "A3\u2013A6 (feature/router variants), A7 (learned benefit routing), A8 (A7 + "
        "S_omega), R1\u2013R3 (router ablations) and F1 (a deliberate failure arm). "
        "A1's harmful share is "
        f"{f4(M('ABL_A1_HARMFUL_SHARE'))}; learned routing in A7 reduces it to "
        f"{f4(M('ABL_A7_HARMFUL_SHARE'))}. F1 produces a mean \u0394 Dice of "
        f"{f4(M('ABL_F1_MEAN_DELTA_DICE'))}, confirming the evaluation detects a broken policy.")
    R.figure("V8_F07_ablation_arms",
             "All 13 arms with mean true \u0394 Dice on routed cases. Blue = A7 (learned "
             "routing), teal = A8 (A7 + post-safety), amber = A1 (always refine), red = F1 "
             "(deliberate failure). The A8 \u2212 A7 paired contrast CI "
             f"[{f4(M('ABL_A7_CI_LOW'), 2)}, {f4(M('ABL_A7_CI_HIGH'), 2)}] includes zero: "
             "**the incremental safety contribution is not established**.",
             width=WIDTH, source="REMEDFILM_ABLATION_AND_PROGRESSION.csv")
    R.figure("ABL02_paired_contrasts_forest",
             "Paired contrasts between selected arms with intervals. Only contrasts whose "
             "interval excludes zero are described as established.",
             width=152.0, source="phase28 arm metrics / ABL02")
    R.table("Selected ablation arms on ROUTER_DEVELOPMENT (n = 4,957). "
            "Full 13-arm provenance is in REMEDFILM_V8_ABLATION_RESULTS.csv.",
            ["Arm", "Routed cases", "Mean \u0394 Dice", "Harmful share", "Benefit capture"],
            [[a, f"{int(M(f'ABL_{a}_ROUTED_CASES')):,}",
              f4(M(f"ABL_{a}_MEAN_DELTA_DICE")),
              f4(M(f"ABL_{a}_HARMFUL_SHARE")),
              f4(M(f"ABL_{a}_BENEFIT_CAPTURE"))]
             for a in ["A0", "A1", "A3", "A5", "A6", "A7", "A8", "F1"]],
            widths=[20, 34, 40, 38, 38], size=7.8,
            note=f"A8 \u2212 A7 CI: [{float(M('ABL_A7_CI_LOW')):.2e}, "
                 f"{float(M('ABL_A7_CI_HIGH')):.2e}], "
                 "excludes zero = NO. The 32.37% = 390/1205 figure in older documents is "
                 "a conditional in-sample policy statistic with zero GPU execution and is "
                 "not used as a headline result in V8.")

    # ---------------- 10 ---------------- #
    R.h1(SECTION_TITLES[9])
    R.p(f"On VAL808 the frozen state machine records {route['decisions']['SKIP']} SKIP and "
        f"{route['decisions']['EXECUTE']} EXECUTE router decisions. The four terminal "
        f"branches are SKIP_GLOBAL {route['branches']['SKIP_GLOBAL']}, "
        f"EXECUTE_THEN_ACCEPT {route['branches']['EXECUTE_THEN_ACCEPT']} and "
        f"EXECUTE_THEN_REJECT {route['branches']['EXECUTE_THEN_REJECT']}; FORCED_SKIP is "
        f"{cr['n'] - sum(route['branches'].values())} on this split (an action was available "
        "for every validation image). Rejection is not an error path \u2014 it is the "
        "designed global fallback when S_omega withholds acceptance.")
    R.table("VAL808 state-machine outcomes and their downstream masks.",
            ["State", "n", "Share", "Output mask"],
            [
                ["FORCED_SKIP", "0", "0.0000", "p_global (no action available)"],
                ["SKIP_GLOBAL", "529", f4(529 / 808), "p_global (router utility below tau_C8)"],
                ["EXECUTE_THEN_ACCEPT", "266", f4(266 / 808), "fused regional candidate"],
                ["EXECUTE_THEN_REJECT", "13", f4(13 / 808), "p_global (safety fallback)"],
            ],
            widths=[46, 18, 24, 82],
            note="Counts from reports/tables/phase27_val808_predictions.csv. "
                 "For all 529 SKIP cases the saved FULL mask is byte-identical to the "
                 "backbone mask.")
    R.p("Error propagation is bounded by construction: outside the ROI the global map is "
        "retained exactly, and any rejected candidate is discarded wholesale. Harm can "
        "therefore only arise on accepted executed cases. Nevertheless "
        f"{M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_HARMFUL')} of 808 images are harmed relative to "
        "the backbone. Because the backbone is in-sample while downstream stages are "
        "out-of-fold, the recorded harm rate is optimistic rather than conservative; V8 "
        "does not repair this asymmetry.")
    R.note("No overstated safety claim",
           "S_omega is trained on `sign(delta_dice)` with BCEWithLogitsLoss. It estimates "
           "whether a refinement improves Dice relative to the backbone, **not** whether a "
           "prediction is clinically correct, whether a lesion is present, or whether the "
           "output is safe for a patient. Any 'clinical safety' reading of the gate is "
           "unsupported.", tone="red")

    # ---------------- 11 ---------------- #
    R.h1(SECTION_TITLES[10])
    R.h2("11.1  Adjudication of the legacy headline value")
    R.p("Three values circulated for VAL808: **0.837290** (ReMedFiLM FULL), **0.837862** "
        "(also labelled FULL in V5\u2013V7) and **0.835079** (GlobalMedFiLM). V8 resolves "
        "them as follows. `0.835079718` is the backbone comparator, not a competing FULL "
        "value. `0.837862` is not a measurement: it is the arithmetic mean of three numbers "
        "hard-coded into the V5/V6/V7 generators (0.837862 / 0.837910 / 0.837815; mean "
        "0.837862333) and was printed as **both** the seed-42 row and the three-seed mean. "
        "No routing policy expressible from the saved masks reproduces it.")
    R.table("Three-seed reconciliation. Genuine values re-aggregated from the frozen "
            "per-sample NPZ archive with the same equal-domain-weight rule.",
            ["Seed", "Frozen NPZ macro Dice", "V5\u2013V7 printed", "Difference"],
            [
                ["42", "0.837289", "0.837862", "\u22120.000573"],
                ["123", "0.838467", "0.837910", "+0.000557"],
                ["3407", "0.837948", "0.837815", "+0.000133"],
                ["**Mean**", "**0.837901**", "0.837862", "+0.000039"],
                ["**SD (ddof=1)**", "**0.000590**", "0.0000475", "\u224812\u00d7 understated"],
            ],
            widths=[24, 52, 46, 48],
            note="Seed 42 from the archive is 0.837289105, agreeing with the saved-mask "
                 "re-score 0.837289686 to 5.81\u00d710\u207b\u2077. All three seeds share one "
                 "pre-trained backbone, so this triplet is descriptive component-"
                 "initialisation stability, not three independent end-to-end replicates.")
    R.p("A second frozen record, `reports/audits/phase29_val808_seedwise_metrics.json`, "
        "gives a genuine but different descriptive triplet (0.837351 / 0.838511 / "
        "0.838000; mean 0.837954, SD 0.000581). Its seed-42 entry reports 268 accepted "
        "cases whereas the saved masks encode 266; those two extra safety decisions were "
        "never persisted separately. V8 **discloses** this variant as genuinely recorded "
        "but not re-derivable, and does **not** select it. V7's impossible routing counts "
        "(183 selected / 165 accepted / 31 rejected) are likewise rejected rather than "
        "reconciled.")
    R.figure("V8_F06_seedwise_deltas",
             "Three downstream seeds on the shared frozen backbone: macro-domain VAL808 Dice "
             "and paired \u0394 Dice versus the frozen G backbone. Descriptive only; no seed "
             "was retrained for V8 and the backbone is common to all three.",
             width=WIDTH, source="frozen three-seed NPZ archive")

    R.h2("11.2  Reproducibility infrastructure")
    R.p("Every V8 number is fetched from `REMEDFILM_V8_RESULTS_REGISTRY.json` (291 records). "
        "Each record carries a metric ID, model identity, active components, population, "
        "split, domain, sample count, run ID, seed, checkpoint digest, config, metric "
        "definition, aggregation rule, source path, source SHA-256, evidence class and "
        "verification status. SHA-256 values are computed from the bytes on disk at build "
        "time; superseded artifacts are moved to `_superseded_v8` rather than deleted. "
        "Five legacy sources with conflicting values are explicitly excluded and their "
        "exclusion reasons recorded.")
    R.note("Host-clock disclosure",
           "The build host clock is not synchronised (NTP leap indicator 3, local CMOS, no "
           "recorded sync), so absolute timestamps carry an unquantified offset. V8 omits "
           "absolute dates and establishes provenance through content digests and "
           "within-run ordering instead.", tone="navy")

    R.h2("11.3  Interpretability and robustness")
    R.p("The router is interpretable at the level of its inputs: 202 frozen, ground-truth-"
        "free numeric features plus a 16-D task embedding, regressed to a scalar predicted "
        "\u0394 Dice and compared against a fixed utility threshold. It sees neither a "
        "learned global feature tensor nor the refined crop. No feature-attribution study "
        "or counterfactual explanation is claimed in V8.")
    R.figure("ROB01_perturbation_degradation",
             "Perturbation robustness: degradation of segmentation quality under the "
             "recorded input perturbations. This is a descriptive stress test, not a "
             "certification of clinical robustness.",
             width=152.0, source="robustness evidence / ROB01")

    # ---------------- 12 ---------------- #
    R.h1(SECTION_TITLES[11])
    R.p("Complexity is reported for the frozen components and for the routed policy. "
        "Expected conditional GMACs integrate over the observed execution frequency; the "
        "always-refine cost is the unconditional upper branch. Parameter counts are "
        "measured from checkpoint state dicts, not estimated.")
    R.table("Verified computational cost. Latency is the recorded p50 for the frozen "
            "runtime; GMACs are analytical for a 3 \u00d7 512 \u00d7 512 input.",
            ["System", "Parameters", "GMACs", "Latency p50 (ms)"],
            [
                ["GlobalMedFiLM (G, backbone)", f"{int(M('EFF_G_PARAMETERS')):,}",
                 f4(M("EFF_G_GMACS"), 4), f4(M("EFF_G_LATENCY_P50_MS"), 2)],
                ["**ReMedFiLM FULL (routed)**", f"**{int(M('EFF_FULL_PARAMETERS')):,}**",
                 f"**{f4(M('EFF_FULL_GMACS'), 4)}**",
                 f"**{f4(M('EFF_FULL_LATENCY_P50_MS'), 2)}**"],
                ["Always-refine (A1) upper branch", "\u2014",
                 f4(M("ABL_STAGE_1_GMACS"), 4), "\u2014"],
            ],
            widths=[62, 36, 36, 36],
            note="An older README quote of 34.72 GMACs for always-refine differs from the "
                 "frozen CSV value 34.7824; V8 uses the CSV and records the visible caveat "
                 "rather than silently harmonising them.")
    R.figure("V8_F01_accuracy_cost",
             "Accuracy versus architectural cost with the canonical ReMedFiLM FULL point "
             f"at Dice {f4(M('INT_MACRO_DOMAIN_EQUAL_WEIGHT_FULL_DICE'))} and "
             f"{f4(M('EFF_FULL_GMACS'), 4)} expected conditional GMACs. **Historical "
             "descriptive comparison**, not a confirmed Pareto frontier: the baseline "
             "protocols are not matched controlled experiments, and V7's point was wrong "
             "on both axes (0.837862 paired with the always-refine 34.72 GMACs).",
             width=WIDTH, source="V8 registry / phase21 compute")
    R.figure("EFF02_latency_breakdown",
             "Recorded latency breakdown by pipeline stage for the frozen runtime.",
             width=146.0, source="REMEDFILM_EFFICIENCY.csv / EFF02")
    R.figure("EFF03_accuracy_vs_parameters",
             "Accuracy against parameter count on a log axis, placing the compact FULL "
             "system in the context of the historical six-model comparison.",
             width=146.0, source="REMEDFILM_EFFICIENCY.csv / EFF03")

    # ---------------- 13 ---------------- #
    R.h1(SECTION_TITLES[12])
    R.h2("13.1  Supported claims")
    R.table("Claims supported by frozen artifacts, and the evidence class that supports each.",
            ["Claim", "Evidence class", "Status"],
            [
                ["ReMedFiLM FULL = G + R_psi + B_phi + S_omega; G is the backbone only",
                 "read-only checkpoint state-dict verification", "**ESTABLISHED**"],
                ["VAL808 paired gain +0.002210 (95% CI excludes zero)",
                 "paired preservation, saved-mask re-score + bootstrap", "**ESTABLISHED**"],
                ["Four inference states with 529 / 266 / 13 outcomes",
                 "frozen Phase 27 prediction table + source code", "**ESTABLISHED**"],
                ["Learned benefit routing reduces harmful refinements vs always-refine",
                 "frozen 13-arm policy comparison (in-sample)", "**DESCRIPTIVE / ESTABLISHED AS POLICY**"],
                ["External direction consistent on 884 images",
                 "frozen external retrospective tables", "**DESCRIPTIVE**"],
                ["Incremental S_omega contribution (A8 \u2212 A7)",
                 "paired CI includes zero", "**NOT ESTABLISHED**"],
                ["C1 learned vs identity FiLM; C3 matched multi-seed baselines",
                 "no controlled study", "**NOT ESTABLISHED**"],
                ["Clinical safety / diagnostic validity",
                 "no clinical study; gate targets sign(\u0394 Dice)", "**NOT CLAIMED**"],
            ],
            widths=[80, 60, 30], size=7.7)

    R.h2("13.2  Limitations")
    R.bullets([
        "The reported gain is small (+0.2210 pp) and concentrated in one of four domains; "
        "97 of 808 images are harmed relative to the backbone.",
        "The backbone is in-sample while refiner, router and safety stages are out-of-fold, "
        "making delta-Q and harm rates optimistic. This asymmetry was recorded, not repaired.",
        "The 13-arm comparison is a policy comparison over frozen outputs, not a causal "
        "retraining ablation; A8 \u2212 A7 does not establish a safety contribution.",
        "Three downstream seeds share one pre-trained backbone, so the seed triplet is not "
        "three independent end-to-end replicates. No matched multi-seed baseline matrix exists.",
        "External evaluation is retrospective, small for the Stones cohort (n = 20, with "
        "HD95/ASSD defined on only 6), and BrEaST patient-level independence is unverifiable.",
        "14 / 14 stone-free external images receive false-positive foreground; the safety "
        "gate does not detect lesion absence.",
        "TEST1683 remains protected and unopened. No prospective test result is reported "
        "and no submission-ready claim of generalisation to a held-out test cohort is made.",
        "The host clock is unsynchronised; absolute timestamps are deliberately omitted.",
    ])

    R.h2("13.3  Experiments still required for submission")
    R.bullets([
        "**C1** \u2014 a matched learned-FiLM versus identity-FiLM controlled comparison "
        "under a common training budget and identical data order.",
        "**C2** \u2014 a causal safety-gate attribution study with a pre-registered primary "
        "endpoint and an adequately powered A8 versus A7 contrast.",
        "**C3** \u2014 a matched multi-seed baseline matrix, with all baselines trained and "
        "evaluated under the identical protocol as the FULL system.",
        "A prospective, authorised TEST1683 evaluation under the frozen protocol, with the "
        "protected split opened only under the corresponding release authority.",
        "External validation with verified patient-level independence, larger stone cohorts, "
        "and a prespecified analysis of the stone-free false-positive failure mode.",
        "Repair or explicitly bound the backbone in-sample / downstream out-of-fold asymmetry, "
        "then re-estimate harm rates and conditional benefit.",
        "A matched accuracy\u2013cost study before any Pareto or efficiency superiority claim.",
    ])
    R.note("Final declaration",
           "ReMedFiLM V8 is an **analysis-only reconstruction**. No model was retrained, no "
           "new inference was run, no frozen split was changed, no checkpoint was modified, "
           "no measurement was fabricated, no diagnosis was invented, no authorisation was "
           "bypassed, and the protected TEST1683 inputs were **not opened**. Where a "
           "required controlled study does not exist, V8 reports NOT_ESTABLISHED rather "
           "than implying completion.", tone="navy")

    # ---------------- appendix ---------------- #
    R.pagebreak()
    h = doc.add_heading("Appendix A.  Deliverables and regeneration", level=1)
    R.sections.append({"number": "A", "title": "Deliverables and regeneration"})
    R.table("V8 deliverables referenced by this report (paths relative to the repository root).",
            ["Artifact", "Purpose"],
            [
                ["`ReMedFiLM_Complete_Scientific_Report_V8.docx` / `.pdf`", "this report"],
                ["`figures/ReMedFiLM_Methodology_V8.svg/.pdf/.png`", "code-verified three-panel methodology figure"],
                ["`figures/ReMedFiLM_Methodology_GitHub_16x9.png`", "16:9 GitHub/README variant"],
                ["`REMEDFILM_V8_RESULTS_REGISTRY.json`", "single numeric source, 291 records"],
                ["`REMEDFILM_V8_INTERNAL_EVALUATION.csv`", "151 provenance-complete internal rows"],
                ["`REMEDFILM_V8_EXTERNAL_EVALUATION.csv`", "44 provenance-complete external rows"],
                ["`REMEDFILM_V8_TRAINING_HISTORY.csv`", "component training histories"],
                ["`REMEDFILM_V8_ABLATION_RESULTS.csv`", "96 ablation provenance rows"],
                ["`REMEDFILM_V8_FIGURE_EVIDENCE_MAP.json`", "33 used / 8 excluded figures"],
                ["`REMEDFILM_V8_METHODOLOGY_ARROWS.json`", "20 verified / 13 corrected arrows"],
                ["`REMEDFILM_V8_RESULT_RECONCILIATION.md`", "0.837290 / 0.837862 / 0.835079 adjudication"],
                ["`V7_TO_V8_CORRECTIONS.md`", "correction log"],
                ["`V8_FINAL_SCIENTIFIC_QA.md` / `V8_PUBLICATION_READINESS.md`", "18-check QA and readiness verdict"],
            ],
            widths=[92, 78], size=7.8)
    R.p("Regeneration is deterministic and analysis-only: "
        "`v8_registry.py` \u2192 `v8_reconciliation.py` \u2192 "
        "`v8_figure_methodology.py` \u2192 `v8_figures_scientific.py` \u2192 "
        "`v8_report.py` \u2192 `export_v8_pdf.ps1` \u2192 `v8_qa.py`. "
        "All scripts live in `full_doc_report/v8_build/` and are driven by the Python "
        "interpreter `.venv/Scripts/python.exe`. Superseded generations are moved to "
        "`full_doc_report/_superseded_v8/` rather than deleted.")

    return R


# --------------------------------------------------------------------------- #
def main() -> None:
    doc = setup_document()
    R = build(doc)
    doc.save(OUT_DOCX)
    manifest = {
        "artifact": "V8_REPORT_CONTENT_MANIFEST",
        "docx": str(OUT_DOCX.relative_to(ROOT)).replace("\\", "/"),
        "sections": R.sections,
        "numbered_section_count": 13,
        "figure_count": R.fig_no,
        "table_count": R.tab_no,
        "figures": R.figures,
        "tables": R.tables,
        "numeric_claims": R.numeric_claims,
        "single_numeric_source": "full_doc_report/REMEDFILM_V8_RESULTS_REGISTRY.json",
        "single_numeric_source_sha256": sha256(FDR / "REMEDFILM_V8_RESULTS_REGISTRY.json"),
        "figure_evidence_map_sha256": sha256(FDR / "REMEDFILM_V8_FIGURE_EVIDENCE_MAP.json"),
        "declaration": {
            "model_retrained": False,
            "new_inference_run": False,
            "TEST1683_opened": False,
            "checkpoint_modified": False,
            "absolute_timestamp_hand_authored": False,
        },
    }
    write_json(MANIFEST, manifest)
    print(f"wrote {OUT_DOCX.name}: {OUT_DOCX.stat().st_size:,} bytes")
    print(f"  numbered sections : {manifest['numbered_section_count']}")
    print(f"  figures           : {R.fig_no}")
    print(f"  tables            : {R.tab_no}")
    print(f"  numeric claims    : {len(R.numeric_claims)}")
    print(f"wrote {MANIFEST.name}")


if __name__ == "__main__":
    main()
