"""ReMedFiLM V9 -- final report completion and export repair.

Takes the existing V9 DOCX in ``full_doc_report/V9/`` (the only artifact that
carries the 33 evidence-backed figures and 24 tables) and applies the V9
scientific corrections, without re-running any generator that would rebuild
content from superseded inputs.

Why this script exists
----------------------
The shipped ``v9_report.py`` is a copy of ``v8_report.py``: it imports
``v9_common`` (a V8 clone), reads ``REMEDFILM_V9_FIGURE_EVIDENCE_MAP.json`` and
``REMEDFILM_V9_METHODOLOGY_ARROWS.json`` which do not exist, and 44 of its 46
registry lookups are absent from the verified 267-record V9 registry.  Running
it therefore cannot reproduce a V9 document.  The existing V9 DOCX is a
relabelled V8 build (identical 194 paragraphs / 24 tables / 33 images, V8->V9
string substitutions only), so it also carries V8 residues and omits the V9
scientific corrections.

This script repairs the artifact in place-style (write-once, new file) and
records every change so the result is auditable.

Applied corrections (each traced to a frozen V9 source)
------------------------------------------------------
  R01  running header says V8 -> V9
  R02  population table column "Status in V8" -> "Status in V9"; TEST1683 row
       reconciled with ``test1683_disclosure`` (historical Phase-39 access
       disclosed, no V9 access, no relabel as untouched)
  R03  registry size corrected 291 -> 267 metric records
  R04  appendix deliverable table rebuilt from files that actually exist
  R05  ISIC-2018 / HAM10000 disposition added from ``ham10000`` registry block
  R06  inference implementation class added from
       ``inference_implementation_class`` (B_HISTORICAL_OFFLINE_CACHED_CANDIDATE_REPLAY,
       deployable_end_to_end_inference = false)
  R07  dual-population compute disclosure added from
       EFF_A8_VAL808_CONDITIONAL_GMAC / EFF_A8_HOLDOUT_CONDITIONAL_GMAC
  R08  operator-supplied conceptual methodology infographic added as a
       numbered figure, with an explicit divergence register from the
       code-verified figure
  R09  references section added, restricted to entries recorded in this
       repository (phase23_prior_art_matrix.csv, ReMedFiLM_V9_Dataset_Guide.md)
  R10  remaining V8 self-references in note boxes corrected to V9

No training, no inference, no checkpoint write, no TEST1683 input access.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

ROOT = Path(__file__).resolve().parents[3]
FDR = ROOT / "full_doc_report"
V9 = FDR / "V9"
REGISTRY = FDR / "REMEDFILM_V9_RESULTS_REGISTRY.json"
OUT_DOCX = FDR / "ReMedFiLM_Complete_Scientific_Report_V9.docx"
OUT_COPY = V9 / "ReMedFiLM_Complete_Scientific_Report_V9.docx"
OUT_PDF = FDR / "ReMedFiLM_Complete_Scientific_Report_V9.pdf"
MANIFEST = V9 / "V9_FINAL_REPORT_MANIFEST.json"

# Pristine V9 DOCX (the artifact to be corrected).  It is kept out of the
# write path so the script stays idempotent: re-running always starts from the
# same bytes rather than from its own previous output.
SRC_DOCX = Path(__file__).resolve().parent / ".pristine_v9_source.docx"
SRC_SHA256 = "945d00fab32b44e554433541df69fbadf1c654fdc143dc2a70f7ca7b46872872"

INFOGRAPHIC_SRC = Path(
    r"C:\Users\user\Downloads\ReMedFiLM Full Inference Methodology Infographic.png"
)
INFOGRAPHIC_DST = V9 / "figures" / "ReMedFiLM_V9_Conceptual_Infographic.png"

REG = json.loads(REGISTRY.read_text(encoding="utf-8"))
METRICS = {m["metric_id"]: m for m in REG["metrics"]}


def M(mid: str):
    """Registry lookup; a missing key is a hard abort (never a silent zero)."""
    if mid not in METRICS:
        raise KeyError(f"registry key absent -- ABORT: {mid}")
    return METRICS[mid]["value"]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# low-level docx helpers (formatting-preserving)
# --------------------------------------------------------------------------- #
def set_para_text(par, text: str) -> None:
    runs = par.runs
    if not runs:
        par.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._element.getparent().remove(r._element)


def replace_in_runs(par, old: str, new: str) -> bool:
    """Replace text inside runs without destroying run/tab structure."""
    hit = False
    for r in par.runs:
        if old in r.text:
            r.text = r.text.replace(old, new)
            hit = True
    return hit


RICH_TOKEN = re.compile(r"(\*\*.+?\*\*|`.+?`)", re.S)


def render_rich(par, text: str) -> None:
    """Render ``**bold**`` and ``\\`mono\\``` inline, preserving run structure.

    Mirrors the document's own ``rich()`` helper so inserted paragraphs look
    native instead of exposing literal markup markers.
    """
    from docx.oxml import OxmlElement

    first = par.runs[0] if par.runs else None
    base_name = first.font.name if first is not None else None
    base_size = first.font.size if first is not None else None
    base_color = first.font.color.rgb if first is not None and first.font.color else None
    for r in list(par.runs):
        r._element.getparent().remove(r._element)
    for tok in RICH_TOKEN.split(text):
        if not tok:
            continue
        bold = mono = False
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            tok, bold = tok[2:-2], True
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            tok, mono = tok[1:-1], True
        run = par.add_run(tok)
        run.bold = bold
        if mono:
            run.font.name = "Consolas"
            rpr = run._r.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rpr.append(rf)
            rf.set(qn("w:ascii"), "Consolas")
            rf.set(qn("w:hAnsi"), "Consolas")
            if base_size is not None:
                run.font.size = Pt(base_size.pt - 0.5)
        elif base_name:
            run.font.name = base_name
        if base_size is not None and not mono:
            run.font.size = base_size
        if base_color is not None:
            run.font.color.rgb = base_color


def set_cell_text(cell, text: str) -> None:
    set_para_text(cell.paragraphs[0], text)
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def note_table(doc, template_tbl, title: str, body: str):
    """Deep-copy a shaded 1x1 note box so styling is identical by construction."""
    new = copy.deepcopy(template_tbl._tbl)
    cell = new.find(qn("w:tr")).find(qn("w:tc"))
    paras = cell.findall(qn("w:p"))
    # first paragraph = bold title, second = body (as in the source template)
    from docx.text.paragraph import Paragraph

    p_title = Paragraph(paras[0], template_tbl)
    p_body = Paragraph(paras[1], template_tbl)
    set_para_text(p_title, title)
    render_rich(p_body, body)
    p_body.runs[0].bold = False if p_body.runs else None
    for extra in paras[2:]:
        cell.remove(extra)
    return new


def clone_heading(doc, template_par, text: str):
    new = copy.deepcopy(template_par._p)
    from docx.text.paragraph import Paragraph

    p = Paragraph(new, template_par._parent)
    set_para_text(p, text)
    return new


def clone_body(doc, template_par, text: str, *, rich_text: bool = True):
    new = copy.deepcopy(template_par._p)
    from docx.text.paragraph import Paragraph

    p = Paragraph(new, template_par._parent)
    if rich_text:
        render_rich(p, text)
    else:
        set_para_text(p, text)
    return new


def find_image_par(paras):
    for p in paras:
        if p._p.findall(".//" + qn("a:blip")):
            return p
    raise RuntimeError("no image paragraph template found")


def clone_figure(doc, template_par, image_path: Path, width_mm: float):
    """Clone an existing centred-image paragraph and repoint it at a new image.

    ``DocumentPart.get_or_add_image`` returns ``(rId, image)``.
    """
    from docx.text.paragraph import Paragraph

    new = copy.deepcopy(template_par._p)
    blip = new.find(".//" + qn("a:blip"))
    if blip is None:
        raise RuntimeError("template figure paragraph has no blip")
    rId, image = doc.part.get_or_add_image(str(image_path))
    blip.set(qn("r:embed"), rId)
    cx = int(Mm(width_mm))
    cy = int(round(cx * image.px_height / image.px_width))
    n_set = 0
    for tag in ("wp:extent", "a:ext"):
        for el in new.findall(".//" + qn(tag)):
            el.set("cx", str(cx))
            el.set("cy", str(cy))
            n_set += 1
    if n_set < 2:
        raise RuntimeError(f"expected wp:extent and a:ext, patched {n_set}")
    return Paragraph(new, template_par._parent), new


def insert_before_next_heading1(doc, start_par, elements):
    """Insert ``elements`` immediately before the next Heading 1 after ``start_par``."""
    cursor = start_par._p
    while True:
        nxt = cursor.getnext()
        if nxt is None:
            raise RuntimeError("reached end of body looking for the next Heading 1")
        if nxt.tag == qn("w:p"):
            pPr = nxt.find(qn("w:pPr"))
            style = pPr.find(qn("w:pStyle")) if pPr is not None else None
            if style is not None and style.get(qn("w:val")) == "Heading1":
                for element in elements:
                    nxt.addprevious(element)
                return
        cursor = nxt


def normalise_tables(doc, text_width_mm: float = 170.0) -> list[str]:
    """Make every table's grid, row cells and width agree, and fit the page.

    The inherited document stores ``tblW = auto`` while individual cells carry
    ``tcW`` values that contradict the ``w:gridCol`` widths (e.g. the "Stage"
    column of Table 2 has a 14 mm grid column but a 42 mm cell width).  Word
    then re-lays the table out, which pushed the first column outside the left
    margin and clipped its header to "age".  This pass makes the declared widths
    consistent and explicit so the rendered layout matches the intent.
    """
    from docx.oxml import OxmlElement
    from docx.shared import Mm as _Mm

    touched = []
    for index, table in enumerate(doc.tables):
        tbl = table._tbl
        grid = tbl.find(qn("w:tblGrid"))
        if grid is None:
            continue
        cols = grid.findall(qn("w:gridCol"))
        if not cols:
            continue
        # current grid widths in mm
        widths = [int(c.get(qn("w:w=")) or c.get(qn("w:w"))) / 56.6929 for c in cols]
        total = sum(widths)
        if total <= 0:
            continue
        # scale to the text block
        factor = text_width_mm / total
        widths = [w * factor for w in widths]
        # enforce a legible minimum, borrowing from the widest column
        MIN_MM = 18.0
        deficit = sum(MIN_MM - w for w in widths if w < MIN_MM)
        if deficit > 0:
            donor = max(range(len(widths)), key=lambda i: widths[i])
            widths = [MIN_MM if w < MIN_MM else w for w in widths]
            widths[donor] -= deficit
            scale = text_width_mm / sum(widths)
            widths = [w * scale for w in widths]
        # write the grid back
        for col, w in zip(cols, widths):
            col.set(qn("w:w"), str(int(round(w * 56.6929))))
        # explicit fixed total width
        tblPr = tbl.tblPr
        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = OxmlElement("w:tblW")
            tblPr.insert(0, tblW)
        tblW.set(qn("w:type"), "dxa")
        tblW.set(qn("w:w"), str(int(round(sum(widths) * 56.6929))))
        # every cell must match its grid column
        for row in table.rows:
            for cell, w in zip(row.cells, widths):
                tcPr = cell._tc.get_or_add_tcPr()
                tcW = tcPr.find(qn("w:tcW"))
                if tcW is None:
                    tcW = OxmlElement("w:tcW")
                    tcPr.insert(0, tcW)
                tcW.set(qn("w:type"), "dxa")
                tcW.set(qn("w:w"), str(int(round(w * 56.6929))))
        touched.append(f"T{index}({len(widths)}cols,{sum(widths):.0f}mm)")
    return touched


def build_static_toc(doc, field_par, pages: dict, template_par):
    """Replace the Word TOC field with a static, accurate contents list.

    ``TablesOfContents.Update()`` never returned on this document (Word spun
    indefinitely with no dialog, twice).  A static list is deterministic and
    still reports real page numbers, because the caller supplies them from a
    first-pass PDF export in which this list already occupies the same space.
    """
    from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
    from docx.text.paragraph import Paragraph

    entries = []
    for p in doc.paragraphs:
        if not (p.style and p.style.name in ("Heading 1", "Heading 2")):
            continue
        t = p.text.strip()
        if not t or t == "Contents":
            continue
        entries.append((1 if p.style.name == "Heading 1" else 2, t))

    anchor = field_par._p
    made = []
    for level, text in entries:
        new = copy.deepcopy(template_par._p)
        par = Paragraph(new, template_par._parent)
        for r in list(par.runs):
            r._element.getparent().remove(r._element)
        pf = par.paragraph_format
        pf.tab_stops.add_tab_stop(Mm(168), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        pf.left_indent = Mm(0 if level == 1 else 5)
        pf.space_after = Pt(1.2)
        pf.space_before = Pt(3 if level == 1 else 0)
        label = text
        r1 = par.add_run(label)
        r1.font.size = Pt(9.0 if level == 1 else 8.6)
        r1.bold = level == 1
        r2 = par.add_run("\t" + str(pages.get(text, "\u2014")))
        r2.font.size = Pt(9.0 if level == 1 else 8.6)
        r2.bold = level == 1
        anchor.addprevious(new)
        made.append(new)
    anchor.getparent().remove(anchor)
    return [e[1] for e in entries]


def export_pages(docx_path: Path, pdf_path: Path) -> dict[str, int]:
    """Export ``docx_path`` to PDF with Word COM and map heading text to page.

    Returns ``{heading_text: page_number}`` for every Heading 1/2 paragraph.
    Uses ``SaveAs2(..., 17)``, the only export path that returned reliably on
    this host (``ExportAsFixedFormat`` and ``TablesOfContents.Update`` both hung).
    """
    import subprocess

    script = Path(__file__).resolve().parent / "_v9_page_probe.ps1"
    script.write_text(
        "param([string]$Src,[string]$Out,[string]$Json)\n"
        "$ErrorActionPreference='Stop'\n"
        "$w=New-Object -ComObject Word.Application\n"
        "$w.Visible=$false; $w.DisplayAlerts=0; $w.AutomationSecurity=3\n"
        "$rows=@()\n"
        "try{\n"
        "  $d=$w.Documents.Open($Src,$false,$true,$false)\n"
        "  $d.Repaginate()\n"
        "  foreach($p in $d.Paragraphs){\n"
        "    $s=$p.Style.NameLocal\n"
        "    if($s -eq 'Heading 1' -or $s -eq 'Heading 2'){\n"
        "      $t=$p.Range.Text.Trim()\n"
        "      if($t.Length -gt 0){ $rows += [pscustomobject]@{t=$t;p=$p.Range.Information(3)} }\n"
        "    }\n"
        "  }\n"
        "  if(Test-Path $Out){ Remove-Item -LiteralPath $Out -Force }\n"
        "  $d.SaveAs2($Out,17)\n"
        "  $d.Close(0)\n"
        "} finally { $w.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($w)|Out-Null }\n"
        "$rows | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $Json -Encoding UTF8\n"
        "if(-not (Test-Path $Out)){ throw 'no pdf' }\n",
        encoding="utf-8",
    )
    json_out = pdf_path.with_suffix(".pages.json")
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
         "-Src", str(docx_path), "-Out", str(pdf_path), "-Json", str(json_out)],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        print(proc.stdout[-2000:])
        print(proc.stderr[-2000:])
        return {}
    if not json_out.exists():
        return {}
    raw = json.loads(json_out.read_text(encoding="utf-8-sig") or "[]")
    if isinstance(raw, dict):
        raw = [raw]
    pages: dict[str, int] = {}
    for row in raw:
        text = (row.get("t") or "").strip()
        page = row.get("p")
        if text and isinstance(page, int) and page > 0 and text not in pages:
            pages[text] = page
    json_out.unlink(missing_ok=True)
    return pages


def main() -> None:
    if not SRC_DOCX.exists():
        raise SystemExit(f"source V9 DOCX absent: {SRC_DOCX}")
    if not INFOGRAPHIC_SRC.exists():
        raise SystemExit(f"infographic absent: {INFOGRAPHIC_SRC}")

    src_sha_before = sha256(SRC_DOCX)
    if src_sha_before != SRC_SHA256:
        raise SystemExit(
            f"pristine V9 source hash mismatch: {src_sha_before} != {SRC_SHA256}"
        )
    v8_docx = FDR / "ReMedFiLM_Complete_Scientific_Report_V8.docx"
    v8_pdf = FDR / "ReMedFiLM_Complete_Scientific_Report_V8.pdf"
    v8_guard = {"docx": sha256(v8_docx), "pdf": sha256(v8_pdf)}

    INFOGRAPHIC_DST.parent.mkdir(parents=True, exist_ok=True)
    if not INFOGRAPHIC_DST.exists():
        shutil.copyfile(INFOGRAPHIC_SRC, INFOGRAPHIC_DST)
    infographic_sha = sha256(INFOGRAPHIC_DST)

    doc = Document(SRC_DOCX)
    body = doc.element.body
    paras = doc.paragraphs
    changes: list[str] = []

    template_note = next(
        t for t in doc.tables
        if len(t.rows) == 1 and len(t.columns) == 1 and "V8" in t.cell(0, 0).text
    )
    h1_template = next(p for p in paras if p.style and p.style.name == "Heading 1")
    h2_template = next(p for p in paras if p.style and p.style.name == "Heading 2")
    body_template = next(
        p for p in paras if p.style and p.style.name == "Normal" and len(p.text) > 200
    )
    fig_template = find_image_par(paras)
    cap_template = next(
        p for p in paras
        if p.style and p.style.name == "Caption" and p.text.startswith("Figure ")
    )

    # ------------------------------------------------------------------ R01
    for section in doc.sections:
        for p in section.header.paragraphs:
            # run-level edit: set_para_text would flatten the right-aligned tab
            if replace_in_runs(p, "V8", "V9"):
                changes.append("R01 running header V8->V9 (run-level, tab preserved)")
        for p in section.footer.paragraphs:
            # pre-existing V8/V9 defect: the tab between the disclaimer and the
            # page field is missing, so "not openedPage 1 of 29" renders joined.
            for r in p.runs:
                if r.text.endswith("opened") and "\tPage " not in r.text:
                    r.text = r.text + "\t"
                    changes.append("R13 footer tab restored before page field")
                    break

    # ------------------------------------------------------- R03 / R10 text
    exact = {
        "Status in V8": "Status in V9",
        "All V8 numbers trace to a single source-linked registry of 291 metric "
        "records.": (
            "All V9 numbers trace to a single source-linked registry of "
            f"{REG['metric_count']} metric records."
        ),
        "V8 also adjudicates a legacy headline value": (
            "V9 also adjudicates a legacy headline value"
        ),
        "No p-values are added in V8 beyond the pre-registered bootstrap intervals.": (
            "No p-values are added in V9 beyond the pre-registered bootstrap intervals."
        ),
        "REMEDFILM_V9_RESULTS_REGISTRY.json (291 records)": (
            f"REMEDFILM_V9_RESULTS_REGISTRY.json ({REG['metric_count']} records)"
        ),
        "REMEDFILM_V8_ABLATION_RESULTS.csv": "REMEDFILM_V9_ABLATION_13ARM.csv",
        "REMEDFILM_V9_ABLATION_RESULTS.csv": "REMEDFILM_V9_ABLATION_13ARM.csv",
        "No history in V8 was regenerated": "No history in V9 was regenerated",
        "V8->V9 issue ledger (ISS-01..ISS-07)": (
            "audit issue ledger carried into V9 (ISS-01..ISS-07)"
        ),
        "used in V9. Values are counts of images": (
            "used in V9. Values are counts of images"
        ),
    }

    REGEN_OLD = (
        "Regeneration is deterministic and analysis-only: v8_registry.py"
    )
    REGEN_NEW = (
        "Regeneration is deterministic and analysis-only. The evidence artifacts "
        "underpinning this report were produced by the frozen V9 registry build; the "
        "report document itself is completed and exported by "
        "v9_build/v9_finalize_report.py, then v9_build/export_v9_final_pdf.ps1, then "
        "verified by v9_build/verify_v9_report.py. Those three scripts are "
        "analysis-only: no training, no inference, no checkpoint write and no "
        "TEST1683 access. Superseded generations are archived rather than deleted. "
        "(Legacy version-8 build scripts referenced by earlier drafts do not "
        "regenerate this document and are not part of the V9 pipeline.)"
    )

    def apply_exact(text: str) -> str:
        for a, b in exact.items():
            if a in text:
                text = text.replace(a, b)
        # generic self-reference repair inside note boxes / prose
        text = re.sub(r"\bV8 reports\b", "V9 reports", text)
        text = re.sub(r"\bV8 records\b", "V9 records", text)
        text = re.sub(r"\bV8 omits\b", "V9 omits", text)
        text = re.sub(r"\bV8 uses\b", "V9 uses", text)
        text = re.sub(r"ReMedFiLM V8 is", "ReMedFiLM V9 is", text)
        text = re.sub(r"\bV8 table and figure\b", "V9 table and figure", text)
        return text

    for p in doc.paragraphs:
        new = apply_exact(p.text)
        if REGEN_OLD in new:
            new = REGEN_NEW
            changes.append("R11 stale V8 regeneration recipe replaced")
        # inherited prose exposes literal `mono` / ** markers; render them
        if ("`" in new or "**" in new) and p.style and p.style.name in (
            "Normal", "List Bullet", "List Number"
        ):
            render_rich(p, new)
            changes.append("R14 inline markup rendered: " + new[:60])
            continue
        if new != p.text:
            set_para_text(p, new)
            changes.append("R03/R10 prose: " + new[:70])
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    new = apply_exact(p.text)
                    new = new.replace("V8->V9 issue ledger", "audit issue ledger (V9)")
                    if new != p.text:
                        set_para_text(p, new)
                        changes.append("R03/R10 table: " + new[:70])

    # ------------------------------------------------------------------ R02
    pop = next(t for t in doc.tables if t.rows[0].cells[0].text.strip() == "Population")
    set_cell_text(pop.rows[0].cells[2], "Status in V9")
    td = REG["test1683_disclosure"]
    assert td["v9_access"] is False
    for row in pop.rows[1:]:
        if row.cells[0].text.strip() == "TEST1683":
            set_cell_text(
                row.cells[2],
                "PROTECTED — historical one-shot Phase-39 access disclosed; "
                "no V9 access; not relabelled as untouched",
            )
            changes.append("R02 TEST1683 disclosure row reconciled")

    # ------------------------------------------------------------------ R04
    appendix = next(
        t for t in doc.tables if t.rows[0].cells[0].text.strip() == "Artifact"
    )
    deliverables = [
        ("ReMedFiLM_Complete_Scientific_Report_V9.docx / .pdf",
         "this report (main report directory)"),
        ("V9/figures/ReMedFiLM_Methodology_Manuscript.png",
         "code-verified three-panel methodology figure (Figure 2)"),
        ("V9/figures/ReMedFiLM_V9_Conceptual_Infographic.png",
         "operator-supplied conceptual inference diagram (Figure 3)"),
        ("V9/figures/ReMedFiLM_Methodology_GitHub_16x9.png",
         "16:9 GitHub/README variant of the verified figure"),
        ("REMEDFILM_V9_RESULTS_REGISTRY.json",
         f"single numeric source, {REG['metric_count']} metric records"),
        ("REMEDFILM_V9_INTERNAL_EVALUATION.csv", "internal evaluation summary rows"),
        ("REMEDFILM_V9_EXTERNAL_EVALUATION.csv", "external evaluation rows"),
        ("REMEDFILM_V9_ABLATION_13ARM.csv", "13-arm ablation summary"),
        ("V9/ReMedFiLM_V9_Results_Registry.json",
         "section-level registry used for narrative adjudication"),
        ("V9/ReMedFiLM_V9_Scientific_Audit.md", "audit issue ledger carried into V9 (ISS-01..ISS-07)"),
        ("V9/ReMedFiLM_V9_Architecture_Code_Map.md",
         "component-to-code map and Mode-B inference classification"),
        ("V9/ReMedFiLM_V9_Efficiency_Reconciliation.md",
         "dual-population GMAC and latency reconciliation"),
        ("V9/ReMedFiLM_V9_HAM10000_Audit.md", "HAM10000 availability audit"),
        ("V9/ReMedFiLM_V9_Dataset_Guide.md", "dataset provenance and resource links"),
        ("V9/ReMedFiLM_V9_Methodology_Figure_Provenance.md",
         "provenance and divergence register for the conceptual infographic"),
        ("V9/V9_FINAL_REPORT_MANIFEST.json", "build manifest, counts and hashes"),
        ("V9/v9_build/v9_finalize_report.py", "this report completion step"),
        ("V9/v9_build/export_v9_final_pdf.ps1", "DOCX->PDF export (Word COM)"),
        ("V9/v9_build/verify_v9_report.py", "post-export verification"),
    ]
    # this run produces the manifest and the PDF; they cannot pre-exist
    produced_here = {
        "ReMedFiLM_Complete_Scientific_Report_V9.docx / .pdf",
        "V9/V9_FINAL_REPORT_MANIFEST.json",
    }
    missing = [
        d for d, _ in deliverables
        if d not in produced_here and not (FDR / d).exists()
    ]
    assert not missing, f"deliverable table would list absent files: {missing}"
    while len(appendix.rows) - 1 > len(deliverables):
        appendix._tbl.remove(appendix.rows[-1]._tr)
    while len(appendix.rows) - 1 < len(deliverables):
        appendix.add_row()
    for i, (art, purpose) in enumerate(deliverables, start=1):
        set_cell_text(appendix.rows[i].cells[0], art)
        set_cell_text(appendix.rows[i].cells[1], purpose)
    changes.append(f"R04 appendix rebuilt with {len(deliverables)} existing deliverables")

    # ------------------------------------------------------------------ R07
    eff = next(
        t for t in doc.tables
        if [c.text.strip() for c in t.rows[0].cells[:2]] == ["System", "Parameters"]
    )
    gmac_holdout = float(M("EFF_A8_HOLDOUT_CONDITIONAL_GMAC"))
    gmac_val = float(M("EFF_A8_VAL808_CONDITIONAL_GMAC"))
    for row in eff.rows[1:]:
        if row.cells[0].text.strip().startswith("ReMedFiLM FULL"):
            set_cell_text(
                row.cells[0],
                f"ReMedFiLM FULL (routed; router-holdout rate, n = 875)",
            )
            set_cell_text(row.cells[2], f"{gmac_holdout:.4f}")
    eff.add_row()
    last = eff.rows[-1]
    set_cell_text(last.cells[0], "ReMedFiLM FULL (routed; VAL808 realized rate, n = 808)")
    set_cell_text(last.cells[1], "4,837,420")
    set_cell_text(last.cells[2], f"{gmac_val:.4f}")
    set_cell_text(last.cells[3], "18.89")
    changes.append("R07 dual-population compute row added")

    # ------------------------------------------------------------------ R08
    # 1) The conceptual figure is physically inserted at the END of Section 2,
    #    i.e. immediately after the existing Figure 5 (the portrait variant).
    #    Its correct reading-order number is therefore 6, and the existing
    #    6..33 shift to 7..34.
    NEW_FIG_NO = 6
    fig_caps = [
        p for p in doc.paragraphs
        if p.style and p.style.name == "Caption"
        and re.match(r"^Figure \d+\.", p.text.strip())
    ]
    for p in sorted(fig_caps, key=lambda q: int(re.match(r"^Figure (\d+)", q.text.strip()).group(1)),
                    reverse=True):
        n = int(re.match(r"^Figure (\d+)", p.text.strip()).group(1))
        if n >= NEW_FIG_NO:
            set_para_text(p, re.sub(r"^Figure \d+\.", f"Figure {n + 1}.", p.text.strip(), count=1))
    changes.append(
        f"R08 existing figures {NEW_FIG_NO}..33 renumbered to {NEW_FIG_NO + 1}..34"
    )

    # 2) locate insertion point: the caption of the verified methodology figure
    cap2 = next(
        p for p in doc.paragraphs
        if p.style and p.style.name == "Caption" and p.text.startswith("Figure 2.")
    )
    div = REG["inference_implementation_class"]
    assert div["deployable_end_to_end_inference"] is False

    h_new = clone_heading(doc, h2_template, "2.6  Conceptual reference diagram and its status")
    p_intro = clone_body(
        doc, body_template,
        f"Figure {NEW_FIG_NO} is the operator-supplied conceptual diagram of the ReMedFiLM FULL "
        "inference system. It is included because it states the intended "
        "four-component design more legibly than any renderer output, and because "
        f"the verified implementation class is **{div['class']}** with "
        f"`deployable_end_to_end_inference = {str(div['deployable_end_to_end_inference']).lower()}`. "
        "It is a conceptual schematic, not a code-verified figure: it must never be "
        "read as evidence that the pipeline executes end-to-end on an arbitrary new "
        "image. Figure 2 remains the authoritative, arrow-by-arrow verified diagram.",
    )
    p_img, img_p = clone_figure(doc, fig_template, INFOGRAPHIC_DST, 168.0)

    cap_new = clone_body(
        doc, cap_template,
        f"Figure {NEW_FIG_NO}.  Conceptual reference schematic of the proposed ReMedFiLM FULL "
        "inference system (operator-supplied infographic; three panels: multi-domain "
        "inputs and task conditioning, the FULL inference system, and the staged "
        "training strategy). PANEL B IS ASPIRATIONAL WITH RESPECT TO THE FROZEN CODE: "
        f"the implementation class is {div['class']}, in which a supplied "
        "out-of-fold refined crop and pre-computed feature vectors replace online "
        "candidate generation. Divergences from the verified figure are listed "
        "immediately below and in ReMedFiLM_V9_Methodology_Figure_Provenance.md.  "
        f"[{INFOGRAPHIC_DST.relative_to(ROOT).as_posix()}; sha256 {infographic_sha[:16]}...]",
    )
    from docx.text.paragraph import Paragraph

    cap_par = Paragraph(cap_new, cap2._parent)
    cap_par.style = doc.styles["Caption"]
    divergence_title = (
        f"Divergence register: conceptual Figure {NEW_FIG_NO} versus verified code "
        "(Figure 2)"
    )
    divergence_title = "Divergence register: conceptual Figure 3 versus verified code (Figure 2)"
    divergence_body = (
        "D1 — Figure 3 shows a single shared task embedding E(t) feeding both the "
        "backbone and the rest of the chain; the code has three separate task "
        "representations (G: 32-D learned embedding, B_phi: 16-D learned embedding, "
        "S_omega: 4-D one-hot).  "
        "D2 — Figure 3 shows B_phi consuming 'global features Fg'; B_phi actually "
        "consumes a 202-D ground-truth-free numeric feature vector plus its own 16-D "
        "embedding (218-D input).  "
        "D3 — Figure 3 shows R_psi emitting a 'delta P' correction added to the "
        "global map; R_psi emits a refined crop probability and fusion is "
        "deterministic window replacement, not addition or alpha blending.  "
        "D4 — Figure 3 shows the refiner being called online; in the canonical "
        "wrapper the refiner module is never invoked, and a cached out-of-fold crop "
        "probability is supplied instead.  "
        "D5 — Figure 3 depicts a single skip route; the code has two distinct skip "
        "states (FORCED_SKIP when no action is available, SKIP_GLOBAL when the router "
        "utility falls below tau_C8).  "
        "D6 — Figure 3 shows ROI composition as '+'; composition is replacement of "
        "p_global inside the expanded ROI only.  "
        "D7 — Figure 3's training panel is directionally correct (sequential, "
        "frozen upstream) but does not show that the three modelled losses differ "
        "(BCE+soft Dice, Huber, BCE-with-logits) and that no joint objective exists."
    )
    note = note_table(doc, template_note, divergence_title, divergence_body)

    # Section 2.6/2.7 belong at the END of Section 2, immediately before
    # "3.  Datasets, splits and evaluation protocol".
    sec3_h1 = next(
        p for p in doc.paragraphs
        if p.style and p.style.name == "Heading 1" and p.text.startswith("3.")
    )
    for element in (h_new, p_intro, img_p, cap_new, note):
        sec3_h1._p.addprevious(element)
    changes.append("R08 conceptual infographic inserted as Figure 3 with divergence register")

    # ------------------------------------------------------------------ R05 / R06
    ham = REG["ham10000"]
    assert ham["status"].startswith("EXTERNAL_SKIN_DATASET_AVAILABLE"), ham["status"]
    ds_table = next(
        t for t in doc.tables if t.rows[0].cells[0].text.strip() == "Dataset"
    )
    ds_table.add_row()
    r = ds_table.rows[-1]
    cls = ham["classes"]
    set_cell_text(r.cells[0], "HAM10000 (ISIC-2018 Task 3 release)")
    set_cell_text(
        r.cells[1],
        f"Dermoscopy / pigmented lesion; {ham['images']:,} images with "
        f"{ham['masks']:,} binary masks; classes "
        + ", ".join(f"{k} {v:,}" for k, v in cls.items()),
    )
    set_cell_text(r.cells[2], f"{ham['licence']}; not used as ground truth")
    set_cell_text(
        r.cells[3],
        "AVAILABLE, NOT EVALUATED — 0 identifier overlap with the internal ISIC "
        "2018 Task-1 splits; no established ReMedFiLM segmentation evaluation",
    )
    changes.append("R05 HAM10000 row added to the source-dataset table")

    sec3 = next(
        p for p in doc.paragraphs
        if p.style and p.style.name == "Heading 2" and p.text.startswith("3.3")
    )
    h_ham = clone_heading(
        doc, h2_template, "3.4  HAM10000: dataset available, segmentation evaluation not established"
    )
    p_ham = clone_body(
        doc, body_template,
        f"The local dermatoscopy collection contains {ham['images']:,} images, "
        f"{ham['masks']:,} binary masks and {ham['metadata_rows']:,} metadata rows "
        f"under {ham['licence']}. Mask geometry is {ham['mask_dimensions'][0]}x"
        f"{ham['mask_dimensions'][1]} with binary values {ham['binary_values']}. "
        f"Its identifier overlap with the internal ISIC 2018 Task-1 manifests is "
        f"{ham['id_overlap_with_internal_isic2018_task1']}. "
        f"Two masks ({', '.join(ham['all_foreground_masks'])}) are degenerate "
        f"all-foreground, and {len(ham['image_exact_duplicate_pairs'])} exact image "
        "duplicate pairs are recorded. Disposition: "
        f"**{ham['status']}**. {ham['reason_not_established']} "
        "No HAM10000 Dice, IoU or boundary metric is reported anywhere in V9, and "
        "the EXTERNAL884 denominator is unchanged.",
    )
    ham_note = note_table(
        doc, template_note, "Why no HAM10000 result is reported",
        "Reporting a segmentation score on this collection would require ground truth "
        "that the local copy does not establish: the images are the Task-3 "
        "classification release, and the accompanying masks carry no provenance, "
        "licence or annotation record. V9 records availability and the audit outcome "
        "instead of manufacturing a metric. A future authorised, properly annotated "
        "external evaluation is the correct next step.",
    )
    # 3.4 must close Section 3, immediately before the Section 4 heading
    insert_before_next_heading1(doc, sec3, [h_ham, p_ham, ham_note])
    changes.append("R05 section 3.4 HAM10000 disposition added")

    # R06 inference implementation class (before section 3 heading)
    h_cls = clone_heading(
        doc, h2_template, "2.7  Verified inference implementation class (Mode B)"
    )
    p_cls = clone_body(
        doc, body_template,
        "The frozen implementation is a **decision, verification and composition "
        f"engine**, not an online pipeline. Verified class: **{div['class']}**; "
        f"`deployable_end_to_end_inference = {str(div['deployable_end_to_end_inference']).lower()}`. "
        f"Evidence: {div['evidence']} Consequence: {div['interpretation']}. "
        "An arbitrary new image cannot be passed to `forward_inference` without "
        "externally supplying the 202-D router features, the refined crop "
        "probability and the 16-D post-candidate safety features. This is disclosed "
        "as an engineering gap, not as a failure of the measured result: every "
        "reported number comes from saved out-of-fold artifacts of exactly this "
        "state machine.",
    )
    sec3_h1._p.addprevious(h_cls)
    sec3_h1._p.addprevious(p_cls)
    changes.append("R06 inference implementation class section added")

    # ------------------------------------------------------------------ R07 prose
    sec12 = next(
        p for p in doc.paragraphs
        if p.style and p.style.name == "Heading 1" and p.text.startswith("12.")
    )
    n_val = int(REG["canonical_result"]["n"])
    n_exec = int(M("ROUTE_DECISION_EXECUTE"))
    n_skip = int(M("ROUTE_DECISION_SKIP"))
    assert n_exec + n_skip == n_val, (n_exec, n_skip, n_val)
    p_dual = clone_body(
        doc, body_template,
        "Two conditional-compute values are reported and must not be conflated. "
        f"The **router-holdout** figure, {gmac_holdout:.4f} GMACs, uses the frozen "
        "ROUTER_HOLDOUT activation frequency (240/875 = 27.43%) and is the "
        "benchmark-design value. The **VAL808 realized** figure, "
        f"{gmac_val:.4f} GMACs, uses the empirical activation frequency of the "
        f"canonical validation population ({n_exec}/{n_val} = "
        f"{100 * n_exec / n_val:.2f}%; {n_skip}/{n_val} skipped). Quoting the "
        "holdout value as the VAL808 cost was an error in earlier versions, "
        "corrected here.",
    )
    sec12._p.addnext(p_dual)
    changes.append("R07 dual-population compute paragraph added")

    # ------------------------------------------------------------------ R09
    appendix_h1 = next(
        p for p in doc.paragraphs
        if p.style and p.style.name == "Heading 1" and p.text.startswith("Appendix A")
    )
    h_ref = clone_heading(doc, h1_template, "References")
    ref_intro = clone_body(
        doc, body_template,
        "Every entry below is recorded inside this repository. Bibliographic "
        "metadata is reproduced from `reports/tables/phase23_prior_art_matrix.csv` "
        "and `full_doc_report/V9/ReMedFiLM_V9_Dataset_Guide.md`; it has not been "
        "independently re-verified against publisher records within this "
        "analysis-only task, and no citation was generated from memory. Entries are "
        "listed alphabetically by first author.",
    )
    refs = [
        "Bernal, J.; Sánchez, F. J.; Fernández-Esparrach, G.; Gil, D.; Rodríguez, C.; "
        "Vilarino, F. (2015). WM-DOVA maps for accurate polyp highlighting in "
        "colonoscopy: Validation vs. saliency maps from physicians. Computerized "
        "Medical Imaging and Graphics 43:99-111. [dataset citation recorded in "
        "ReMedFiLM_V9_Dataset_Guide.md]",
        "Butoi, V. I.; Gonzalez Ortiz, J. J.; Ma, T.; Sabuncu, M. R. (2023). "
        "UniverSeg: Universal Medical Image Segmentation. ICCV 2023, pp. 21438-21451. "
        "doi:10.1109/ICCV51070.2023.01960",
        "Chow, C. K. (1970). On Optimum Recognition Error and Reject Tradeoff. IEEE "
        "Transactions on Information Theory 16(1). doi:10.1109/TIT.1970.1054406",
        "Codella, N. C. F.; et al. (2019). Skin Lesion Analysis Toward Melanoma "
        "Detection 2018: A Challenge Hosted by the International Skin Imaging "
        "Collaboration (ISIC). arXiv:1902.03368. [recorded in "
        "ReMedFiLM_V9_Dataset_Guide.md]",
        "Graves, A. (2016). Adaptive Computation Time for Recurrent Neural Networks. "
        "arXiv:1603.08983. doi:10.48550/arXiv.1603.08983",
        "Hor, S.; Qian, Y.; Pilanci, M.; Arbabian, A. (2024). Adaptive Inference: "
        "Theoretical Limits and Unexplored Opportunities. arXiv:2402.04359. "
        "doi:10.48550/arXiv.2402.04359",
        "Isensee, F.; Jaeger, P. F.; Kohl, S. A. A.; Petersen, J.; Maier-Hein, K. H. "
        "(2021). nnU-Net: a self-configuring method for deep learning-based "
        "biomedical image segmentation. Nature Methods 18:203-211. "
        "doi:10.1038/s41592-020-01008-z",
        "Jha, D.; et al. (2020). Kvasir-SEG: A Segmented Polyp Dataset. MultiMedia "
        "Modeling (MMM), pp. 451-462. [recorded in ReMedFiLM_V9_Dataset_Guide.md]",
        "Künzel, S. R.; Sekhon, J. S.; Bickel, P. J.; Yu, B. (2019). Metalearners for "
        "estimating heterogeneous treatment effects using machine learning. PNAS "
        "116(10). doi:10.1073/pnas.1804597116",
        "Ma, J.; He, Y.; Li, F.; Han, L.; et al. (2024). Segment Anything in Medical "
        "Images. Nature Communications 15:654. doi:10.1038/s41467-024-44824-z",
        "Raposo, D.; Ritter, S.; Richards, B.; Lillicrap, T.; Humphreys, P.; "
        "Santoro, A. (2024). Mixture-of-Depths: Dynamically Allocating Compute in "
        "Transformer-Based Language Models. arXiv:2404.02258. "
        "doi:10.48550/arXiv.2404.02258",
        "Russell, S.; Wefald, E. (1991). Principles of Metareasoning. Artificial "
        "Intelligence 49(1-3). doi:10.1016/0004-3702(91)90015-C",
        "Shen, H.; et al. (2022). Med-DANet: Dynamic Architecture Network for "
        "Efficient Medical Volumetric Segmentation. ECCV 2022. "
        "doi:10.1007/978-3-031-19803-8_30",
        "Tschandl, P.; Rosendahl, C.; Kittler, H. (2018). The HAM10000 dataset, a "
        "large collection of multi-source dermatoscopic images of common pigmented "
        "skin lesions. Scientific Data 5:180161. [recorded in "
        "ReMedFiLM_V9_Dataset_Guide.md]",
        "Viola, P.; Jones, M. (2001). Rapid Object Detection Using a Boosted Cascade "
        "of Simple Features. CVPR 2001. doi:10.1109/CVPR.2001.990517",
        "Wang, M.; Ding, H.; Wang, M.; et al. (2023). SegRefiner: Towards "
        "Model-Agnostic Segmentation Refinement with Discrete Diffusion Process. "
        "NeurIPS 2023. doi:10.48550/arXiv.2312.12425",
        "Wang, X.; Yu, F.; Dou, Z.-Y.; Darrell, T.; Gonzalez, J. E. (2018). SkipNet: "
        "Learning Dynamic Routing in Convolutional Networks. ECCV 2018. "
        "doi:10.48550/arXiv.1711.09485",
    ]
    appendix_h1._p.addprevious(h_ref)
    appendix_h1._p.addprevious(ref_intro)
    anchor = ref_intro
    for item in refs:
        p = clone_body(doc, body_template, item)
        anchor.addnext(p)
        anchor = p
    changes.append(f"R09 references section added ({len(refs)} repository-recorded entries)")

    # ------------------------------------------------------- R12 static TOC
    sec = doc.sections[0]
    text_w = (sec.page_width.mm - sec.left_margin.mm - sec.right_margin.mm)
    touched = normalise_tables(doc, text_w)
    changes.append(
        f"R15 table geometry normalised to the {text_w:.0f} mm text block "
        f"({len(touched)} tables): {', '.join(touched[:6])}..."
    )

    # Two passes.  Pass 1 keeps the Word TOC *field* so that page positions are
    # identical to the final layout; the resulting PDF is used only to read the
    # page number on which each heading landed.  Pass 2 replaces the field with
    # a static contents list carrying those exact numbers.
    toc_field = None
    for p in doc.paragraphs:
        if p._p.findall(".//" + qn("w:instrText")):
            for it in p._p.findall(".//" + qn("w:instrText")):
                if "TOC" in (it.text or ""):
                    toc_field = p
                    break
        if toc_field is not None:
            break
    if toc_field is None:
        raise RuntimeError("TOC field not found; cannot build a static contents list")

    draft = V9 / "v9_build" / ".v9_toc_pass1.docx"
    draft_pdf = V9 / "v9_build" / ".v9_toc_pass1.pdf"
    doc.save(str(draft))
    pages = export_pages(draft, draft_pdf)
    if not pages:
        raise RuntimeError("pass-1 PDF export failed; cannot resolve TOC page numbers")

    before = [p.text.strip() for p in doc.paragraphs
              if p.style and p.style.name in ("Heading 1", "Heading 2")]
    missing = [t for t in before if t and t != "Contents" and t not in pages]
    if missing:
        raise RuntimeError(f"headings missing from pass-1 PDF: {missing[:5]}")
    toc_titles = build_static_toc(doc, toc_field, pages, body_template)
    changes.append(
        f"R12 Word TOC field replaced with a static contents list "
        f"({len(toc_titles)} entries, real page numbers from pass-1 export)"
    )

    # ------------------------------------------------------------------ save
    assert OUT_DOCX.parent == FDR
    doc.save(str(OUT_DOCX))
    if OUT_COPY != OUT_DOCX:
        shutil.copyfile(OUT_DOCX, OUT_COPY)
    draft.unlink(missing_ok=True)
    draft_pdf.unlink(missing_ok=True)

    # ---------------------------------------------------------------- verify
    assert sha256(SRC_DOCX) == SRC_SHA256, "pristine source V9 DOCX was modified"
    assert OUT_DOCX.exists() and OUT_DOCX.stat().st_size > 0, "delivered DOCX missing"
    assert OUT_COPY.exists() and OUT_COPY.stat().st_size == OUT_DOCX.stat().st_size, (
        "organised V9 copy missing or truncated"
    )
    assert {"docx": sha256(v8_docx), "pdf": sha256(v8_pdf)} == v8_guard, "V8 output modified"

    chk = Document(OUT_DOCX)
    texts = "\n".join(p.text for p in chk.paragraphs)
    table_text = "\n".join(
        c.text for t in chk.tables for row in t.rows for c in row.cells
    )
    all_text = texts + "\n" + table_text
    residual = [
        m.group(0) for m in re.finditer(r"\bV8\b", all_text)
        if True
    ]
    fig_caps = [
        p.text for p in chk.paragraphs
        if p.style and p.style.name == "Caption" and p.text.startswith("Figure ")
    ]
    numbers = [int(re.match(r"Figure (\d+)\.", t).group(1)) for t in fig_caps]
    tab_caps = [
        p.text for p in chk.paragraphs
        if p.style and p.style.name == "Caption" and p.text.startswith("Table ")
    ]
    tab_numbers = [int(re.match(r"Table (\d+)\.", t).group(1)) for t in tab_caps]

    pdf_pages = None
    if OUT_PDF.exists():
        import pymupdf

        with pymupdf.open(OUT_PDF) as _pdf:
            pdf_pages = len(_pdf)

    manifest = {
        "artifact": "V9_FINAL_REPORT_MANIFEST",
        "version": "V9",
        "docx": OUT_DOCX.relative_to(ROOT).as_posix(),
        "docx_copy": OUT_COPY.relative_to(ROOT).as_posix(),
        "docx_bytes": OUT_DOCX.stat().st_size,
        "docx_sha256": sha256(OUT_DOCX),
        "pdf": OUT_PDF.relative_to(ROOT).as_posix() if OUT_PDF.exists() else None,
        "pdf_bytes": OUT_PDF.stat().st_size if OUT_PDF.exists() else None,
        "pdf_pages": pdf_pages,
        "pdf_sha256": sha256(OUT_PDF) if OUT_PDF.exists() else None,
        "source_docx": SRC_DOCX.relative_to(ROOT).as_posix(),
        "source_docx_sha256": src_sha_before,
        "v8_preserved": {
            "docx_sha256": v8_guard["docx"],
            "pdf_sha256": v8_guard["pdf"],
        },
        "registry": REGISTRY.relative_to(ROOT).as_posix(),
        "registry_sha256": sha256(REGISTRY),
        "registry_metric_count": REG["metric_count"],
        "conceptual_infographic": {
            "path": INFOGRAPHIC_DST.relative_to(ROOT).as_posix(),
            "sha256": infographic_sha,
            "bytes": INFOGRAPHIC_DST.stat().st_size,
            "origin": "operator-supplied file, copied byte-identically",
            "figure_number": NEW_FIG_NO,
            "status": "CONCEPTUAL_NOT_CODE_VERIFIED",
            "inference_class": div["class"],
            "divergences": 7,
        },
        "counts": {
            "figures": len(fig_caps),
            "tables": len(tab_caps),
            "word_tables": len(chk.tables),
            "inline_images": len(chk.inline_shapes),
            "headings": sum(
                1 for p in chk.paragraphs
                if p.style and p.style.name.startswith("Heading")
            ),
            "references": len(refs),
        },
        "figure_numbers_sequential": numbers == list(range(1, len(numbers) + 1)),
        "table_numbers_sequential": tab_numbers == list(range(1, len(tab_numbers) + 1)),
        "residual_v8_tokens": residual,
        "changes": changes,
        "verification": {
            "registry_keys_resolved": True,
            "ham10000_disclosed": "HAM10000" in all_text,
            "mode_b_disclosed": "B_HISTORICAL_OFFLINE_CACHED_CANDIDATE_REPLAY" in all_text,
            "dual_compute_disclosed": f"{gmac_val:.4f}" in all_text,
            "references_present": "References" in texts,
            "source_v9_docx_unmodified": True,
            "v8_outputs_unmodified": True,
        },
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps(manifest["counts"], indent=2))
    print("figures sequential:", manifest["figure_numbers_sequential"],
          "| tables sequential:", manifest["table_numbers_sequential"])
    print("residual V8 tokens:", residual)
    print("docx:", OUT_DOCX, OUT_DOCX.stat().st_size, "bytes")
    print("sha256:", manifest["docx_sha256"])


if __name__ == "__main__":
    main()