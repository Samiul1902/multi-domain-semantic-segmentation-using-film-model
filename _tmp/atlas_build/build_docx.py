"""Assemble the Research Results Atlas (.docx) from atlas_data.json + figures."""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / "atlas_data.json").read_text(encoding="utf-8"))
OUT = Path(r"D:\Softfors\jup\reports\atlas")
OUT.mkdir(parents=True, exist_ok=True)
DOCX = OUT / "RA_MEDFILM_BARR_Research_Results_Atlas.docx"

NAVY = RGBColor(0x1F, 0x3B, 0x63)
BLUE = RGBColor(0x2E, 0x6F, 0x9E)
GREY = RGBColor(0x55, 0x5B, 0x66)
RED = RGBColor(0xB0, 0x3A, 0x2E)
TEAL = RGBColor(0x1E, 0x7A, 0x70)

doc = Document()

# page setup
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(1.8)
sec.left_margin = Cm(2.0); sec.right_margin = Cm(2.0)

st = doc.styles["Normal"]
st.font.name = "Calibri"; st.font.size = Pt(10)
st.paragraph_format.space_after = Pt(4)
st.paragraph_format.line_spacing = 1.1

for name, size, color, before, after in (
        ("Heading 1", 15, NAVY, 14, 6),
        ("Heading 2", 11.5, BLUE, 10, 4),
        ("Heading 3", 10.5, NAVY, 8, 3)):
    s = doc.styles[name]
    s.font.name = "Calibri"; s.font.size = Pt(size); s.font.bold = True
    s.font.color.rgb = color
    s.paragraph_format.space_before = Pt(before)
    s.paragraph_format.space_after = Pt(after)
    s.paragraph_format.keep_with_next = True


# --------------------------------------------------------------------------- #
def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def table_borders(table, color="B0BCCD", size=4):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def cell_margins(table, t=30, b=30, l=85, r=85):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", t), ("bottom", b), ("left", l), ("right", r)):
        el = OxmlElement(f"w:{side}"); el.set(qn("w:w"), str(val)); el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader"); el.set(qn("w:val"), "true"); trPr.append(el)
    el2 = OxmlElement("w:cantSplit"); trPr.append(el2)


_NUMRE = re.compile(r"[+\-\u2212]?\d[\d,]*\.?\d*(?:[eE][+\-\u2212]?\d+)?")


def _numeric(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return True
    s = str(v).strip()
    if s.startswith("["):
        return True
    if s.endswith("%"):
        return True
    return bool(_NUMRE.fullmatch(s))


def add_table(headers, rows, widths=None, font=7.2, header_bg="1F3B63",
              align_right_from=1, zebra=True, caption=None):
    if caption:
        p = doc.add_paragraph()
        r = p.add_run(caption)
        r.bold = True; r.font.size = Pt(8.5); r.font.color.rgb = NAVY
        p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    table_borders(t); cell_margins(t)
    # column alignment: numeric columns right, text columns left
    col_num = []
    for i in range(len(headers)):
        vals = [r[i] for r in rows if r[i] not in (None, "", "—")]
        col_num.append(bool(vals) and all(_numeric(v) for v in vals))
    hdr = t.rows[0]
    repeat_header(hdr)
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        c.text = ""
        p = c.paragraphs[0]
        run = p.add_run(str(h)); run.bold = True; run.font.size = Pt(font)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if col_num[i] else WD_ALIGN_PARAGRAPH.LEFT
        shade(c, header_bg)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            run = p.add_run("" if val is None else str(val))
            run.font.size = Pt(font)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if col_num[i] else WD_ALIGN_PARAGRAPH.LEFT
            if zebra and ri % 2 == 1:
                shade(cells[i], "EEF2F7")
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_figure(path, caption, max_w=16.0, max_h=19.0):
    p = Path(path)
    if not p.exists():
        add_note(f"[MISSING FIGURE FILE] {path}")
        return
    w, h = Image.open(p).size
    width = max_w
    if width * (h / w) > max_h:
        width = max_h / (h / w)
    doc.add_picture(str(p), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp = doc.add_paragraph()
    r = cp.add_run(caption)
    r.italic = True; r.font.size = Pt(8); r.font.color.rgb = GREY
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(8)


def add_note(text, color=GREY):
    p = doc.add_paragraph()
    r = p.add_run(text); r.italic = True; r.font.size = Pt(8.2); r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(4)
    return p


def para(text, size=10, bold=False, color=None, after=4):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.bold = bold
    if color is not None:
        r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(after)
    return p


def bullets(items, size=9.5):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(it); r.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(2)


def banner(text, sub=None):
    t = doc.add_table(rows=1, cols=1)
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.columns[0].width = Cm(17.0)
    c = t.rows[0].cells[0]
    c.width = Cm(17.0)
    shade(c, "1F3B63")
    c.text = ""
    p = c.paragraphs[0]
    r = p.add_run(text); r.bold = True; r.font.size = Pt(20)
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(4)
    if sub:
        p2 = c.add_paragraph()
        r2 = p2.add_run(sub); r2.font.size = Pt(10.5)
        r2.font.color.rgb = RGBColor(0xDB, 0xE4, 0xEE)
        p2.paragraph_format.space_after = Pt(14)


def footer():
    sec0 = doc.sections[0]
    sec0.different_first_page_header_footer = True
    f = sec0.footer
    p = f.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("RA-MedFiLM-BARR · Research Results Atlas · HEAD ")
    r.font.size = Pt(7.5); r.font.color.rgb = GREY
    r2 = p.add_run(D["meta"]["git_head"][:10]); r2.font.size = Pt(7.5); r2.font.color.rgb = GREY
    r3 = p.add_run("   ·   Page "); r3.font.size = Pt(7.5); r3.font.color.rgb = GREY
    run = p.add_run()
    run.font.size = Pt(7.5); run.font.color.rgb = GREY
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    run._r.append(f1); run._r.append(it); run._r.append(f2)


# formatting helpers
def f4(x): return "—" if x is None else f"{x:.4f}"
def f3(x): return "—" if x is None else f"{x:.3f}"
def f2(x): return "—" if x is None else f"{x:.2f}"
def pc(x): return "—" if x is None else f"{100*x:.1f}%"
def ci(lo, hi): return f"[{lo:.4f}, {hi:.4f}]"
def sci(x):
    if x is None: return "—"
    return f"{x:+.2e}" if abs(x) < 1e-4 else f"{x:+.4f}"
def ci2(lo, hi):
    if abs(lo) < 1e-4 and abs(hi) < 1e-4:
        return f"[{lo:+.2e}, {hi:+.2e}]"
    return f"[{lo:+.4f}, {hi:+.4f}]"
def kfmt(n): return f"{n:,}"

# =========================================================================== #
# TITLE PAGE
# =========================================================================== #
banner("RA-MedFiLM-BARR — Research Results Atlas",
       "Consolidated verified evidence · Phases 21, 27–30, 33–36 and historical Phase 39")
para("A supervisor-ready consolidation of existing experimental evidence. No model was trained, "
     "no frozen evidence was altered, and TEST1683 was not accessed during this work.",
     size=9.5, color=GREY, after=10)

add_table(["Field", "Value"], [
    ["Repository", D["meta"]["repository"]],
    ["Git HEAD", D["meta"]["git_head"]],
    ["Scope", D["meta"]["scope"]],
    ["Evidence policy", D["meta"]["evidence_policy"]],
    ["Populations", "TRAIN 5,832 · VAL 808 · TEST 1,683 (locked) · ROUTER_DEVELOPMENT 4,957 · "
                    "ROUTER_HOLDOUT 875 · EXTERNAL 884"],
    ["Non-goals", "No training, no TEST reopening, no authorization change, no new experimental results"],
], widths=[3.4, 13.4], font=8, align_right_from=9, caption=None)

para("Evidence-class legend", size=9, bold=True, color=NAVY, after=2)
add_table(["Class", "Meaning"], [
    ["REAL", "Measured on real data under a frozen protocol (VAL808 or ROUTER_* populations)."],
    ["SYNTHETIC_BENCHMARK", "Measured on fixture weights / synthetic inputs. Never a segmentation result."],
    ["MIXED_LABELLED", "A table/figure that places real accuracy beside synthetic cost, with each column labelled."],
    ["MISSING_EVIDENCE", "The claim has no supporting real experiment; the gap is named explicitly."],
], widths=[4.2, 12.6], font=8, align_right_from=9)

para("Contents", size=9, bold=True, color=NAVY, after=2)
bullets([
    "Executive summary",
    "1. Model progression and comparability limits",
    "2. Thirteen-arm ablation, paired contrasts and confidence intervals",
    "3. Six-model evaluation matrix (Dice, IoU, Precision, Recall, HD95)",
    "4. Three-seed historical reproducibility and limitations",
    "5. Accuracy versus compute, parameters and latency",
    "6. Per-domain and per-sample performance distributions",
    "7. Interpretability and robustness visualisations",
    "8. Qualitative segmentation examples and failure cases",
    "9. Historical TEST evaluation and its missing comparative endpoint",
    "10. Missing-evidence matrix for C1, C2 and C3",
    "Appendix A — Table and figure provenance index",
    "Appendix B — Unavailable sources and metrics",
    "Appendix C — Evidence classes, populations and known discrepancies",
], size=9)

doc.add_page_break()

# =========================================================================== #
# EXECUTIVE SUMMARY
# =========================================================================== #
doc.add_heading("Executive summary", level=1)
para("This atlas consolidates the verified experimental record of RA-MedFiLM-BARR. It separates three "
     "things that are routinely conflated: real data results (VAL808, ROUTER_DEVELOPMENT, ROUTER_HOLDOUT, "
     "EXTERNAL 884, historical TEST1683), architectural cost, and synthetic performance benchmarks. "
     "No number below is extrapolated from another population.")

bullets([
    "Six-model VAL808 macro-domain Dice: Global MedFiLM 0.8351 > DeepLabV3+ 0.8277 > Transformer/MiT 0.8224 "
    "> U-Net++ 0.7920 > Attention U-Net 0.7890 > U-Net 0.7878.",
    "Paired domain-stratified bootstrap (2,000 draws, seed 42): Global MedFiLM − U-Net = +0.0472 "
    "[0.0340, 0.0606]; − Attention U-Net = +0.0460 [0.0339, 0.0592]; − U-Net++ = +0.0431 [0.0311, 0.0559]; "
    "− Transformer/MiT = +0.0127 [0.0029, 0.0226]; − DeepLabV3+ = +0.0074 [−0.0020, 0.0183] (CI includes zero).",
    "RA-MedFiLM-BARR FULL (seed 42) reaches macro Dice 0.8373 on VAL808, a +0.00221 [+0.00113, +0.00330] "
    "preservation delta over the global reference (Phase 27).",
    "Thirteen-arm ablation (ROUTER_DEVELOPMENT, n = 4,957, K = 1,239): A8 harmful activation share 32.37%; "
    "the only frozen matched contrast A8 vs A7 is +1.6×10⁻⁵ [−1.4×10⁻⁵, +5.1×10⁻⁵] — no detectable mean gain.",
    "Three-seed descriptive reproducibility: macro ΔDice +0.00221 / +0.00339 / +0.00287 (mean +0.00282, "
    "SD 0.00059); the three seeds share one frozen global backbone and are not independent replications.",
    "ROUTER_HOLDOUT (n = 875): global 0.92855, A8 0.93029, Δ +0.00174 [0.00112, 0.00240], non-inferiority "
    "margin 0.005 → preservation asserted (Phase 30).",
    "Phase 33 failure prevalence: low overlap 10.06% (88/875), harmful activation 12.92% (31/240), "
    "missed benefit 0% (0/635), execute-then-reject 1.67% (4/240); KUB carries 73/88 and 26/31.",
    "Historical TEST1683 (one-shot, v1.2): macro Dice 0.8314 — ISIC 0.8869 (n=735), BUSI 0.8504 (n=174), "
    "KVASIR 0.8507 (n=216), KUB 0.7377 (n=558). Descriptive only; no comparative endpoint exists.",
    "C1, C2 and C3 remain NOT_ESTABLISHED. C1 has 0/6 runs and pending institutional authorization.",
])

# =========================================================================== #
# SECTION 1
# =========================================================================== #
_h = doc.add_heading("1. Model progression and comparability limits", level=1); _h.paragraph_format.page_break_before = True
para("The programme moves from conventional segmentation baselines (Phase 20A/20B) to a shared "
     "task-conditioned global model (Global MedFiLM, Phase 21) and then to the BARR system "
     "(Global + Regional refiner + Benefit router + Post-safety, Phase 25/26, evaluated in Phase 27). "
     "Every entry below is a frozen checkpoint evaluated on the same VAL808 population.")

rows = []
for r in D["s1"]["rows"]:
    rows.append([r["model"], r["phase"], kfmt(r["params"]),
                 "—" if r["gmacs"] is None else f"{r['gmacs']:.2f}",
                 "—" if r["best_epoch"] is None else r["best_epoch"],
                 f4(r["macro_dice"]), f4(r["macro_iou"]), r["status"].replace("_", " ")])
add_table(["Model", "Phase", "Params", "GMACs", "Best ep.", "Macro Dice", "Macro IoU", "Status"],
          rows, widths=[5.0, 1.2, 1.8, 1.6, 1.3, 1.8, 1.7, 2.4], font=7.4,
          caption="Table 1.1 — Frozen VAL808 performance across the model progression")

rows = []
for r in D["s1"]["rows"]:
    rows.append([r["model"], f4(r["dice_ISIC"]), f4(r["dice_BUSI"]), f4(r["dice_KVASIR"]), f4(r["dice_KUB"])])
add_table(["Model", "ISIC (357)", "BUSI (84)", "KVASIR (87)", "KUB (280)"], rows,
          widths=[6.2, 2.6, 2.6, 2.6, 2.6], font=7.6,
          caption="Table 1.2 — Per-domain Dice on VAL808 (domain n in header)")
add_figure(HERE / "figures/F01_progression.png",
           "Figure 1.1 — Macro-domain Dice with parameter counts. BARR FULL is the Phase 27 diagnostic "
           "evaluation; Lite is excluded because no real-data evaluation exists.")

doc.add_heading("Comparability limits", level=2)
bullets([
    "Phase 21 inherits 24/24 protocol fields from the Phase 20 shared baseline protocol (phase4_v3 "
    "manifests, 512 px RGB, BCE-Dice 0.5/0.5, AdamW 1e-4/1e-4, cosine T_max 100, batch 4/8, AMP, seed 42, "
    "early stop 15, selection phase20_macro_domain_mean_dice_v1, threshold 0.5, 2,000-draw bootstrap seed 42). "
    "Only architecture and experiment identity differ.",
    "The five conventional baselines originate from Phase 20A/20B and the shared evaluation contract is the "
    "same; the artifacts do not establish that every baseline's training run was byte-identical to Phase 21. "
    "Differences are therefore descriptive.",
    "Macro-domain Dice is the unweighted mean of four per-domain means. ISIC (357) and KUB (280) therefore "
    "weigh the same as BUSI (84) and KVASIR (87); pooled Dice is descriptive only and is never the sole summary.",
    "There is no architecture-matched control (same backbone, FiLM on/off). No causal attribution to FiLM is "
    "permitted from this table; that is the purpose of C1, which is not executed.",
    "VAL808 is a development/validation population. It is not TEST1683 and cannot substitute for it.",
])

# =========================================================================== #
# SECTION 2
# =========================================================================== #
_h = doc.add_heading("2. Thirteen-arm ablation, paired contrasts and confidence intervals", level=1); _h.paragraph_format.page_break_before = True
para("Phase 28 evaluates thirteen arms on ROUTER_DEVELOPMENT (n = 4,957; 875 ROUTER_HOLDOUT rows excluded) "
     "at a fixed activation budget K = 1,239 (25%). A0 is global-only and A1 is always-refine; A2–A5 are "
     "routing-signal comparators; A6/A7/A8 are the learned router, the router with a resource cost, and the "
     "router plus post-safety; R1–R3 and F1 are trained component variants.")

SHORT_DEF = {
    "A0": "global only (no routing/refinement)", "A1": "always refine (full budget)",
    "A2": "random routing (seeded null)", "A3": "entropy routing",
    "A4": "margin routing", "A5": "predicted-ROI-size routing",
    "A6": "learned paired-gain routing", "A7": "A6 + resource cost U = Δ̂ − λC",
    "A8": "A7 + post-safety S_ω (canonical)", "R1": "router without deep features (width 26)",
    "R2": "router without task_id (width 202)", "R3": "router, scalar-only features (width 10)",
    "F1": "refiner without p_global input channel",
}
rows = []
for a in D["s2"]["arms"]:
    rows.append([a["arm"], SHORT_DEF.get(a["arm"], a["definition"][:46]),
                 kfmt(a["n_routed"]), f"{a['mean_delta']:+.4f}", pc(a["harmful_share"]),
                 a["role"].replace("_", " ").title()])
add_table(["Arm", "Definition", "n routed", "Mean ΔDice", "Harmful", "Role"], rows,
          widths=[1.1, 6.2, 1.7, 2.2, 1.7, 4.0], font=7.0,
          caption="Table 2.1 — Thirteen-arm ablation (arm-level point summaries; ROUTER_DEVELOPMENT, n = 4,957)")

rows = []
for c in D["s2"]["contrasts"]:
    rows.append([c["contrast"], kfmt(c["n"]), sci(c["mean_diff"]), ci2(c["lo"], c["hi"]),
                 "YES" if c["excludes_zero"] else "NO (includes 0)"])
add_table(["Contrast", "n", "Paired mean Δ", "95% bootstrap CI", "Excludes zero?"], rows,
          widths=[3.8, 1.4, 2.6, 5.4, 3.4], font=7.4,
          caption="Table 2.2 — Paired contrasts with 95% bootstrap CIs (2,000 replicates, seed 42)")
add_figure(HERE / "figures/F02_ablation.png",
           "Figure 2.1 — Arm-level mean ΔDice and harmful activation share. F1 (refiner without p_global) "
           "is catastrophic and compresses the linear scale; its exact value is −0.03259.")
add_figure(HERE / "figures/F03_contrasts.png",
           "Figure 2.2 — Paired contrast forest plot. A8 vs A7 is the only frozen matched contrast; its CI "
           "includes zero.")

doc.add_heading("What the contrasts do and do not establish", level=2)
bullets([
    "Removing deep global features (R1), task conditioning (R2) or all deep taps (R3) significantly reduces "
    "routed ΔDice relative to A6: −0.00098 [−0.00128, −0.00070], −0.00151 [−0.00181, −0.00123] and "
    "−0.00150 [−0.00181, −0.00121]. These are descriptive component-isolation contrasts, not a causal claim "
    "about the deployed system.",
    "A7 and A6 have identical arm-level summaries because at λ = 0.25 the resource term did not change "
    "membership. A8 differs from A7 only through the safety fallback (1,239 executed, 1,205 accepted, 34 "
    "fallbacks). The paired A8 vs A7 difference is +1.6×10⁻⁵ [−1.4×10⁻⁵, +5.1×10⁻⁵] — no detectable mean gain.",
    "F1 (refiner without the p_global input channel) collapses to −0.03259 mean routed ΔDice with 68.85% "
    "harmful activations; the p_global channel is functionally necessary in this design.",
    "Only A7 vs A8 is a frozen, pre-registered matched contrast. R1–R3 and F1 are explicitly "
    "PRIMARY_REFERENCE_NOT_PRE_REGISTERED descriptive rows. Multiplicity: descriptive, no post-hoc correction.",
    "The population is ROUTER_DEVELOPMENT, a subset of TRAIN5832. These are in-sample results relative to the "
    "global backbone and must not be read as held-out generalisation.",
])

# =========================================================================== #
# SECTION 3
# =========================================================================== #
_h = doc.add_heading("3. Six-model evaluation matrix", level=1); _h.paragraph_format.page_break_before = True
para("All six checkpoints are frozen and evaluated on VAL808 (n = 808) with the same evaluation contract "
     "(threshold 0.5, src.metrics.evaluation_metrics, 2,000-draw domain-stratified bootstrap, seed 42). "
     "Dice and IoU are the published macro-domain values. Precision, Recall and HD95 are the unweighted mean "
     "of the four per-domain means computed from the per-image table; this derivation reproduces the published "
     "macro Dice exactly for all six models, which validates it.")

rows = []
for r in D["s3"]["models"]:
    rows.append([r["model"], kfmt(r["params"]), f4(r["dice"]), f4(r["iou"]),
                 f4(r["precision"]), f4(r["recall"]),
                 f"{r['hd95']:.2f} ({r['hd95_valid_n']})"])
add_table(["Model", "Params", "Dice", "IoU", "Precision", "Recall", "HD95 px (valid n)"], rows,
          widths=[5.0, 2.0, 1.6, 1.6, 1.8, 1.6, 3.2], font=7.4,
          caption="Table 3.1 — Six-model VAL808 evaluation matrix (macro-domain)")

rows = []
for r in D["s3"]["models"]:
    rows.append([r["model"], f4(r["dice_ISIC"]), f4(r["dice_BUSI"]), f4(r["dice_KVASIR"]), f4(r["dice_KUB"])])
add_table(["Model", "ISIC", "BUSI", "KVASIR", "KUB"], rows,
          widths=[6.4, 2.4, 2.4, 2.4, 2.4], font=7.6,
          caption="Table 3.2 — Per-domain Dice on VAL808")

rows = []
for r in D["s3"]["global_domain"]:
    rows.append([r["domain"], kfmt(r["n"]), f4(r["dice"]), f4(r["iou"]), f4(r["precision"]),
                 f4(r["recall"]), f"{r['hd95']:.2f}",
                 "—" if r["dice_ci_low"] is None else f"[{r['dice_ci_low']:.4f}, {r['dice_ci_high']:.4f}]"])
add_table(["Domain", "n", "Dice", "IoU", "Precision", "Recall", "HD95", "Dice 95% CI"], rows,
          widths=[2.0, 1.4, 1.7, 1.7, 1.9, 1.7, 1.6, 4.2], font=7.2,
          caption="Table 3.3 — Global MedFiLM per-domain metrics with Dice confidence intervals")
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase21_global_medfilm\comparison\metric_matrix_dice.png"),
           "Figure 3.1 — Published Dice matrix: six models × four domains (VAL808). Reused unchanged.")
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase21_global_medfilm\comparison\paired_bootstrap_forest.png"),
           "Figure 3.2 — Published paired-bootstrap forest plot for the six-model comparison.")

doc.add_heading("Reading the matrix", level=2)
bullets([
    "Global MedFiLM has the highest Dice (0.8351) and IoU (0.7448). DeepLabV3+ is second on Dice (0.8277) "
    "and IoU (0.7412), and it has higher precision (0.8613 vs 0.8495) and a lower HD95 (39.55 vs 44.22 px). "
    "Dice and boundary accuracy therefore rank the models differently; neither alone is the whole picture.",
    "The paired bootstrap separates Global MedFiLM from U-Net, Attention U-Net, U-Net++ and Transformer/MiT "
    "(all CIs exclude zero) but not from DeepLabV3+ (+0.0074 [−0.0020, 0.0183]).",
    "HD95 is reported with its valid n (789–808). Images with empty predictions have undefined HD95 and "
    "precision; those cells are excluded from the mean and the valid count is shown, not silently imputed.",
    "KUB is the hardest domain for every model (0.764 for Global MedFiLM); ISIC is the easiest (0.897).",
    "No architecture-matched control exists, so these differences are not a causal FiLM effect.",
])

# =========================================================================== #
# SECTION 4
# =========================================================================== #
_h = doc.add_heading("4. Three-seed historical reproducibility and limitations", level=1); _h.paragraph_format.page_break_before = True
para("Phase 29 re-runs the BARR pipeline under seeds 42, 123 and 3,407 on VAL808. The table is descriptive: "
     "the phase explicitly records that no numeric reproducibility pass/fail gate exists and that no best seed "
     "was selected or ranked.")

rows = []
for m in D["s4"]["metrics"]:
    rows.append([m["metric"], f4(m["s42"]), f4(m["s123"]), f4(m["s3407"]),
                 f4(m["mean"]), f4(m["sd"]), f4(m["range"])])
add_table(["Metric", "Seed 42", "Seed 123", "Seed 3407", "Mean", "SD (ddof=1)", "Range"], rows,
          widths=[5.0, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9], font=7.2,
          caption="Table 4.1 — Three-seed descriptive summary on VAL808")
add_figure(HERE / "figures/F04_seeds.png",
           "Figure 4.1 — Macro ΔDice by seed with mean and ±1 SD. All three seeds are positive.")

doc.add_heading("Limitations that must travel with these numbers", level=2)
bullets([
    "The three seeds share one frozen global backbone: macro_global_dice is identical across seeds to "
    "1.4×10⁻¹⁶ (0.8350789601074979). Seed-to-seed variation therefore covers only the downstream components, "
    "not backbone initialisation. They are not independent replications of the full pipeline.",
    "The spread is tiny (SD 0.00059 on ΔDice) and all three seeds are positive, but three seeds cannot "
    "support a meaningful variance estimate or a significance claim.",
    "No numeric reproducibility gate was applied; the phase records 'NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE'. "
    "Reporting a pass/fail verdict here would invent a criterion that does not exist.",
    "No best-seed selection, ranking or seed cherry-picking was performed (best_seed = null, ranking_performed = false).",
])

# =========================================================================== #
# SECTION 5
# =========================================================================== #
_h = doc.add_heading("5. Accuracy versus compute, parameters and latency", level=1); _h.paragraph_format.page_break_before = True
para("Accuracy is real (VAL808). Parameters and GMACs are architectural properties of the frozen models. "
     "Latency and memory are SYNTHETIC_BENCHMARK measurements on fixture weights from Phase D. The three are "
     "shown together but never merged into a single scientific claim.")

rows = []
for r in D["s5"]["rows"]:
    rows.append([r["model"], kfmt(r["params"]), f"{r['gmacs']:.2f}", f4(r["macro_dice"]),
                 f"{r['forward_p50_ms']:.2f}", f"{r['peak_alloc_mib']:.1f}"])
add_table(["Model", "Params", "GMACs", "Macro Dice (real)", "Fwd p50 ms*", "Peak MiB*"], rows,
          widths=[5.4, 2.0, 1.8, 2.6, 2.2, 2.0], font=7.4,
          caption="Table 5.1 — Real accuracy beside architectural cost and synthetic latency (*SYNTHETIC_BENCHMARK)")
add_figure(HERE / "figures/F05_accuracy_cost.png",
           "Figure 5.1 — Left: real VAL808 accuracy versus analytical GMACs. Right: synthetic forward latency "
           "(Phase D). The two panels are different evidence classes and are not a single accuracy-cost law.")

doc.add_heading("Cost accounting and definitional cautions", level=2)
bullets([
    "Analytical MACs are a lower bound over Conv2d and Linear layers at 1×3×512×512; GroupNorm, SiLU, "
    "pooling, bilinear interpolation, FiLM modulation and sigmoid are excluded.",
    "Global MedFiLM is the lightest model in the panel (31.55 G) and still achieves the highest Dice; "
    "U-Net++ is the most expensive (137.94 G) and does not. Parameter count and accuracy are not monotonic.",
    "Phase 30 reports A8's analytical average cost as 32.4379 G at a realised activation fraction of 27.43%; "
    "A7 is 32.4379 G. S_ω does not save compute — it trades a small number of fallbacks for safety, not for speed.",
    "Phase D latency is measured on randomly initialised fixture weights (forward p50 11.8–35.1 ms; full "
    "pipeline p50 15.1–101.0 ms; peak allocation 208.6–712.2 MiB). It is not a trained-model latency claim.",
    "The manuscript source fig10_accuracy_vs_cost_source.csv reports 'FULL execute path' at 18.89 ms (n = 1000), "
    "which corresponds to a forward-only definition, while Phase D's pipeline p50 is ~88 ms. This is a "
    "definitional difference, not a contradiction; the atlas uses Phase D for latency and states the definition.",
])

# =========================================================================== #
# SECTION 6
# =========================================================================== #
_h = doc.add_heading("6. Per-domain and per-sample performance distributions", level=1); _h.paragraph_format.page_break_before = True
para("Aggregate Dice hides the shape of the distribution. The table and figure below use the per-image VAL808 "
     "scores of Global MedFiLM (n = 808) and the Phase 27 per-domain preservation deltas.")

rows = []
for q in D["s6"]["global_quartiles"]:
    rows.append([q["domain"], kfmt(q["n"]), f4(q["mean"]), f4(q["sd"]), f4(q["p05"]),
                 f4(q["median"]), f4(q["p95"])])
add_table(["Domain", "n", "Mean", "SD", "p05", "Median", "p95"], rows,
          widths=[2.6, 1.6, 2.0, 2.0, 2.0, 2.2, 2.0], font=7.6,
          caption="Table 6.1 — Per-image Dice distribution by domain (Global MedFiLM, VAL808)")
add_figure(HERE / "figures/F06_distributions.png",
           "Figure 6.1 — Left: per-image Dice violins by domain. Right: Phase 27 per-domain ΔDice with 95% "
           "bootstrap CIs (2,000 replicates).")
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase21_global_medfilm\failure\dice_distribution.png"),
           "Figure 6.2 — Published per-model Dice distribution and failure panel (VAL808). Reused unchanged.")

doc.add_heading("Distributional findings", level=2)
bullets([
    "KUB has the lowest mean (0.764) and the widest lower tail; ISIC has the highest mean (0.897). "
    "The macro-domain mean is therefore dominated by KUB's behaviour despite equal domain weighting.",
    "Phase 27 per-domain preservation deltas: KUB +0.00745 [0.00455, 0.01011] (CI excludes zero), "
    "ISIC +0.00089 [−0.00021, 0.00203], KVASIR +0.00040 [−0.00236, 0.00374], BUSI +0.00009 [0.00000, 0.00027]. "
    "Only KUB shows a clearly positive preservation effect.",
    "No per-sample TEST distribution is available: the historical Phase 39 result artifact contains only "
    "per-domain mean and median Dice, not the per-sample table.",
])

# =========================================================================== #
# SECTION 7
# =========================================================================== #
_h = doc.add_heading("7. Interpretability and robustness visualisations", level=1); _h.paragraph_format.page_break_before = True
para("Phase 35 provides descriptive model-mechanism evidence on VAL808 across four evidence families that are "
     "explicitly never merged (I1 FiLM parameters, I2 gradient saliency, I3 ROI/regional behaviour, "
     "I4 router feature attribution). Phase 36 provides development-set synthetic-perturbation robustness "
     "evidence on the same 808 images.")

add_figure(Path(r"D:\Softfors\jup\reports\figures\phase35_interpretability\phase35_f1_film_gamma_heatmap.png"),
           "Figure 7.1 — Phase 35: FiLM γ heatmap across the five sites and four tasks (descriptive).", max_h=12)
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase35_interpretability\phase35_f3_task_embedding_geometry.png"),
           "Figure 7.2 — Phase 35: task-embedding geometry. Task identity is separable in embedding space.", max_h=12)
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase35_interpretability\phase35_f5_saliency_self_consistency.png"),
           "Figure 7.3 — Phase 35: gradient-saliency self-consistency (descriptive mechanism evidence).", max_h=12)

rows = [[w["domain"], kfmt(w["n_samples"]), f4(w["worst_image_delta_Dice_min"]),
         f4(w["worst_image_delta_Dice_mean"])] for w in D["s7"]["p36_worst_by_domain"]]
add_table(["Domain", "n", "Worst-sample ΔDice (min)", "Worst-sample ΔDice (mean)"], rows,
          widths=[3.0, 2.0, 5.4, 5.4], font=7.6,
          caption="Table 7.1 — Phase 36 worst-case per-sample ΔDice by domain (VAL808, synthetic perturbations)")

add_figure(Path(r"D:\Softfors\jup\reports\figures\phase36_robustness_v1_23\R1_image_perturbation_mean_paired_delta_dice_heatmap.png"),
           "Figure 7.4 — Phase 36: mean paired ΔDice heatmap over image perturbations (16 conditions × domains).", max_h=13)
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase36_robustness_v1_23\R2_severity_curves_noise_blur_resolution.png"),
           "Figure 7.5 — Phase 36: severity curves for noise, blur and resolution.", max_h=12)
add_figure(Path(r"D:\Softfors\jup\reports\figures\phase36_robustness_v1_23\R5_worst_case_delta_dice_distribution_by_domain.png"),
           "Figure 7.6 — Phase 36: worst-case ΔDice distribution by domain.", max_h=12)

c = D["s7"]["p36_counters"]
add_note(f"Phase 36 scope: {kfmt(c['unique_raw_val_images'])} clean VAL images, "
         f"{kfmt(c['perturbed_g_forwards'])} perturbed forwards, {kfmt(c['test_reads'])} TEST reads, "
         f"{kfmt(c['router_holdout_reads'])} ROUTER_HOLDOUT reads, {kfmt(c['training'])} training runs, "
         f"{kfmt(c['optimizer_steps'])} optimizer steps. Clean-equivalence gate: "
         f"{'PASS' if D['s7']['p36_clean_equiv'] else 'FAIL'} (max |ΔDice| = 0.0).")

# =========================================================================== #
# SECTION 8
# =========================================================================== #
_h = doc.add_heading("8. Qualitative segmentation examples and failure cases", level=1); _h.paragraph_format.page_break_before = True
para("Two distinct qualitative sources exist and must not be merged. The internal gallery is drawn from "
     "VAL808 and compares six models on the same images. The external panel is drawn from the EXTERNAL 884 "
     "cohort (CVC 612 / BrEaST 252 / Stones 20) and illustrates BARR refinement outcomes. They are different "
     "populations with different acquisition characteristics.")

add_figure(Path(r"D:\Softfors\jup\reports\figures\phase21_global_medfilm\gallery\gallery_six_model_KUB.png"),
           "Figure 8.1 — Internal VAL808 gallery (KUB): rows are samples; columns are image, ground truth, "
           "U-Net, Attention U-Net, U-Net++, DeepLabV3+, Transformer/MiT and Global MedFiLM.", max_w=15, max_h=20)

rows = []
for r in D["s8"]["external_rows"]:
    rows.append([r["row_label"], r["sample_id"], f3(float(r["global_dice"])), f3(float(r["barr_dice"])),
                 f"{float(r['delta_pp']):+.1f} pp"])
add_table(["Case", "Sample", "Global Dice", "BARR Dice", "Δ"], rows,
          widths=[6.2, 2.6, 2.6, 2.6, 2.2], font=7.4,
          caption="Table 8.1 — External qualitative case selection (CVC-ClinicDB; EXTERNAL 884)")
add_figure(Path(r"D:\Softfors\jup\paper_doc\figures\fig08_main_qualitative.png"),
           "Figure 8.2 — External qualitative refinement examples: accepted beneficial, accepted harmful, "
           "rejected, non-selected and stone-free false-positive cases (EXTERNAL 884).", max_h=15)
add_figure(Path(r"D:\Softfors\jup\paper_doc\figures\fig09_failure_analysis.png"),
           "Figure 8.3 — External failure taxonomy counts (EXTERNAL 884).", max_h=12)

doc.add_heading("Internal failure analysis (Phase 33, ROUTER_HOLDOUT)", level=2)
bullets([
    "Low overlap: 88/875 = 10.06% (cutoff A8 Dice ≤ 0.82553, the global 10th percentile).",
    "Harmful router activation: 31/240 = 12.92% of EXECUTE rows. Missed benefit: 0/635 SKIP rows. "
    "Execute-then-reject: 4/240 = 1.67%.",
    "Concentration: KUB contributes 73/88 low-overlap cases and 26/31 harmful activations; ISIC contributes "
    "15 low-overlap, 5 harmful and all 4 execute-then-reject; BUSI and KVASIR contribute none.",
    "Phase 33 marks BOUNDARY_ERROR, COMPONENT_ANALYSIS and QUALITATIVE_GALLERY as INELIGIBLE, so no internal "
    "failure image panel exists. The external panel above is the only available qualitative failure evidence, "
    "and it belongs to a different population.",
])

# =========================================================================== #
# SECTION 9
# =========================================================================== #
_h = doc.add_heading("9. Historical TEST evaluation and its missing comparative endpoint", level=1); _h.paragraph_format.page_break_before = True
para("Phase 39 opened TEST1683 once. The v1.2 run completed and produced a descriptive result for the single "
     "BARR pipeline. The result is one-shot, post-protocol technical recovery evidence with two disclosed "
     "pre-outcome failures, and it has no comparative endpoint.")

rows = [[d["domain"], kfmt(d["n"]), f4(d["dice_mean"]), f4(d["dice_median"])] for d in D["s9"]["per_domain"]]
rows.append(["MACRO (unweighted mean of domains)", "1,683", f4(D["s9"]["macro_dice"]), "—"])
add_table(["Domain", "n", "Dice mean", "Dice median"], rows,
          widths=[7.4, 2.2, 3.0, 3.0], font=7.6,
          caption="Table 9.1 — Historical Phase 39 TEST1683 descriptive result (one-shot, v1.2)")
add_figure(HERE / "figures/F09_test.png",
           "Figure 9.1 — TEST1683 per-domain mean Dice with sample counts. Macro 0.8314.")

c = D["s9"]["counters"]
add_table(["Counter", "Value"], [
    ["test_image_reads", kfmt(c["test_image_reads"])],
    ["test_gt_reads", kfmt(c["test_gt_reads"])],
    ["clean_g_forwards", kfmt(c["clean_g_forwards"])],
    ["b_phi_forwards", kfmt(c["b_phi_forwards"])],
    ["r_psi_forwards", kfmt(c["r_psi_forwards"])],
    ["s_omega_forwards", kfmt(c["s_omega_forwards"])],
    ["metric_evaluations", kfmt(c["metric_evaluations"])],
], widths=[6.0, 4.0], font=7.6, caption="Table 9.2 — Phase 39 v1.2 execution counters")

doc.add_heading("What TEST does not contain", level=2)
bullets([
    "No IoU, Precision, Recall, HD95 or per-sample table is present in the result artifact. Only per-domain "
    "mean and median Dice exist. Those metrics are reported here as unavailable, not estimated.",
    "No comparative endpoint exists: there is no C1-T/C1-C arm, no C2 router/safety ablation and no C3 "
    "protocol-faithful baseline on TEST. The result describes one pipeline; it cannot rank models on TEST.",
    "The result is descriptive and must not be presented as a significance test or a model comparison.",
])

doc.add_heading("Access reconciliation: historical record versus recent zero-read claims", level=2)
rows = [[a["revision"], a["stage"], "YES" if a["inference_started"] else "NO", a["reads"], a["result"]]
        for a in D["s9"]["access"]]
add_table(["Revision", "Terminal stage", "Inference started", "TEST reads", "Result"], rows,
          widths=[1.8, 3.4, 3.0, 5.2, 3.2], font=7.2,
          caption="Table 9.3 — Phase 39 access chain")
para("Reconciliation. The recent coding-verification work made zero TEST reads, and that statement is true "
     "for that work: it used synthetic fixtures and redirected temporary roots only. It is not a statement "
     "about the whole project. Historically, v1.0 failed at model load before any TEST access; v1.1 started "
     "TEST inference and failed in the science loop; v1.2 read all 1,683 images and 1,683 ground-truth masks "
     "and produced the result above. The one-shot attempt is consumed. TEST must not be reopened, and the "
     "historical v1.2 result stands as the only TEST evidence.")

# =========================================================================== #
# SECTION 10
# =========================================================================== #
_h = doc.add_heading("10. Missing-evidence matrix for C1, C2 and C3", level=1); _h.paragraph_format.page_break_before = True
para("The programme's three central causal claims are not established. The matrix below names the required "
     "evidence, what exists, and the exact blocker. No synthetic chain test is counted as evidence for a "
     "scientific claim.")

rows = [[r["claim"], r["required"], r["available"], r["blocker"], r["status"]] for r in D["s10"]["rows"]]
add_table(["Claim", "Required evidence", "Available", "Blocker", "Status"], rows,
          widths=[3.4, 3.6, 3.6, 4.2, 2.2], font=6.6,
          caption="Table 10.1 — Missing-evidence matrix for C1, C2 and C3")
add_figure(HERE / "figures/F10_missing.png",
           "Figure 10.1 — Missing-evidence matrix. Teal = present, red = absent.", max_w=14)

doc.add_heading("C1 — FiLM attribution", level=2)
para("Required: six matched C1-T/C1-C runs (seeds 42, 123, 3,407) with identical initial backbone weights, "
     "the frozen optimizer/scheduler/selection protocol, TRAIN5832 for optimisation and VAL808 for selection. "
     "Available: the matched-arm constructor and a synthetic three-epoch chain test (CHAIN_SOUND). Zero real "
     "runs exist. The RC4 institutional trust root is absent, institutional approval is PENDING, no signatory "
     "is identified and key custody is not established. There is also no licence or ethics record in the "
     "repository. C1 is therefore blocked by authorization, not by software.")
doc.add_heading("C2 — BARR router/safety causal ablation", level=2)
para("Required: a pre-registered matched ablation of the router and safety components with approval. "
     "Available: BARR-M1 is design-ready but not approved; the executed analysis is a policy comparison, not "
     "a causal ablation, and it is in-sample with zero GPU. C2 is NOT_ESTABLISHED.")
doc.add_heading("C3 — Protocol-faithful baselines", level=2)
para("Required: a baseline matrix trained under the full frozen protocol. Available: EXT-03, 15/15 complete, "
     "but every run used a reduced protocol (Adam 1e-3, BCE-only, no augmentation) and must never be cited as "
     "protocol-faithful. C3 is NOT_ESTABLISHED.")

# =========================================================================== #
# APPENDIX A
# =========================================================================== #
_h = doc.add_heading("Appendix A — Table and figure provenance index", level=1); _h.paragraph_format.page_break_before = True
para("Every table and figure in this atlas is listed below with its source artifact(s), population, sample "
     "count and evidence status. The same index is provided in machine-readable form "
     "(atlas_table_figure_index.json / .csv).")

rows = []
for t in D["tables"]:
    rows.append([t["id"], t["section"], t["title"], t["population"], ("—" if not t["n"] else t["n"]), t["status"]])
add_table(["ID", "§", "Table", "Population", "n", "Status"], rows,
          widths=[1.3, 0.9, 8.0, 3.4, 1.2, 2.2], font=6.4,
          caption="Table A.1 — Table index")

rows = []
for f in D["figures"]:
    rows.append([f["id"], f["section"], f["title"], f["population"], f["status"]])
add_table(["ID", "§", "Figure", "Population", "Status"], rows,
          widths=[1.5, 0.9, 8.6, 3.6, 2.4], font=6.4,
          caption="Table A.2 — Figure index")

# =========================================================================== #
# APPENDIX B
# =========================================================================== #
_h = doc.add_heading("Appendix B — Unavailable sources and metrics", level=1); _h.paragraph_format.page_break_before = True
para("The following items were searched for and are not available. They are reported explicitly rather than "
     "invented or proxied from another population.")

bullets([
    "Lite (depthwise) real-data VAL808 Dice/IoU: no real training or evaluation was ever executed; only a "
    "synthetic chain test exists.",
    "TEST1683 IoU, Precision, Recall, HD95 and per-sample records: absent from the Phase 39 result artifact.",
    "TEST1683 comparative endpoint (C1, C2, C3): never run; TEST is one-shot and consumed.",
    "Internal qualitative failure gallery: Phase 33 marks QUALITATIVE_GALLERY INELIGIBLE.",
    "C1 matched runs (0/6), C2 causal ablation, C3 protocol-faithful baselines: not established.",
    "Licence/ethics record and institutional authorization: no record exists in the repository.",
    "A single consistent latency definition across the manuscript and Phase D: the manuscript source uses a "
    "forward-only definition; Phase D reports pipeline latency. Both are reported with their definitions.",
])

doc.add_heading("Appendix C — Evidence classes, populations and known discrepancies", level=2)
add_table(["Population", "n", "Role", "Used in"], [
    ["TRAIN", "5,832", "Optimisation", "Phases 20/21/27/29 (training)"],
    ["VAL", "808", "Checkpoint selection + development evaluation", "Phases 21/27/29/30/35/36"],
    ["TEST", "1,683", "Protected one-shot evaluation", "Phase 39 v1.2 only"],
    ["ROUTER_DEVELOPMENT", "4,957", "Router/ablation development", "Phase 28"],
    ["ROUTER_HOLDOUT", "875", "Held-out router evaluation", "Phase 30/33"],
    ["EXTERNAL", "884", "External domain-shift stress test", "CVC 612 / BrEaST 252 / Stones 20"],
], widths=[3.4, 1.6, 6.8, 5.2], font=7.4, caption="Table C.1 — Populations and their roles")
bullets([
    "Known discrepancy 1: the manuscript fig10 latency (FULL execute 18.89 ms, n = 1000) is forward-only; "
    "Phase D pipeline p50 is ~88 ms. Both are reported; neither replaces the other.",
    "Known discrepancy 2: earlier summaries described TEST as never opened. The correct statement is that the "
    "recent coding-verification work made zero reads, while the historical one-shot v1.2 evaluation did open "
    "TEST1683 and produced the descriptive result in §9.",
    "Known discrepancy 3: Phase 36's own release attestation sets requires_v1_23_smoke=false and binds the "
    "v1.14 smoke as historical runtime evidence. That is a governance fact about the robustness run, not a "
    "scientific result, and it is recorded here for transparency.",
    "No claim in this atlas is a statistical significance claim from seed 42 alone, and no scientific phase "
    "is declared passed.",
])

footer()
doc.save(str(DOCX))
print("WROTE", DOCX, DOCX.stat().st_size, "bytes")
print("paragraphs", len(doc.paragraphs), "tables", len(doc.tables), "inline_shapes", len(doc.inline_shapes))
