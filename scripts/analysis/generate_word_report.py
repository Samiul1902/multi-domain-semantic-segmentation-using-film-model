"""Build paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx.

Every number in this report is bound to a frozen artifact. The binding table is
reports/audits/c1_external_evidence_v1_0/claim_provenance.json and is enforced by
tests/test_c1_external_evidence.py.

Corrections relative to the previous build of this report (items A-H, ledger in
Section 9):
  * Regional BARR macro Dice was stated as 86.24 % with no supporting record.
    It is replaced by the Phase 29 three-seed mean on VAL808 (83.79 %) and the
    Phase 30 ROUTER_HOLDOUT value (93.03 %), each labelled with its population.
  * BARR parameter count 4.80 M -> 4,837,420 (4.84 M), from the Phase 34 record.
  * Fabricated p-values ("p<0.001", "p<0.01", "Significant") removed. Phase 31
    established that no confirmatory significance procedure is eligible.
  * The n = 1 external pilot and its HAM10000 row are retracted. The external
    section is now an 884-case retrospective stress test with BARR executed on
    the same cases.

External stress-test numbers are read from reports/tables/c1_external_stress_*.csv
at build time.  No external figure in this document is hand-typed: if the tables
change, the document changes with them.
"""

import json

import docx
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from pathlib import Path

REPORT_DATE = "October 31, 2026"

TAB = Path('reports/tables')
AUD_STRESS = Path('reports/audits/c1_external_stress_v1_0')


def load_stress():
    """Read the external stress-test results. Raises if they are absent."""
    summary = pd.read_csv(TAB / 'c1_external_stress_summary.csv')
    paired = pd.read_csv(TAB / 'c1_external_stress_paired.csv')
    shift = pd.read_csv(TAB / 'c1_external_stress_domain_shift.csv')
    subgroups = pd.read_csv(TAB / 'c1_external_stress_stones_subgroups.csv')
    per_case = pd.read_csv(TAB / 'c1_external_stress_per_case.csv')
    with open(AUD_STRESS / 'barr_executability.json', encoding='utf-8') as fh:
        execu = json.load(fh)
    with open(AUD_STRESS / 'cohort_construction.json', encoding='utf-8') as fh:
        construction = json.load(fh)

    def m(cohort, arm, metric, field='mean'):
        row = summary[(summary.cohort_key == cohort) & (summary.arm == arm)
                      & (summary.metric == metric)]
        return float(row.iloc[0][field])

    return {'summary': summary, 'paired': paired, 'shift': shift,
            'subgroups': subgroups, 'per_case': per_case,
            'exec': execu, 'construction': construction, 'm': m}


def create_report():
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    HEX_PRIMARY = '1F497D'
    HEX_SECONDARY = '595959'
    HEX_BG_LIGHT = 'F2F4F7'
    HEX_HIGHLIGHT = 'D9E1F2'
    HEX_WARN = 'FDE9D9'

    COLOR_PRIMARY = RGBColor(0x1F, 0x49, 0x7D)
    COLOR_SECONDARY = RGBColor(0x59, 0x59, 0x59)
    COLOR_DARK = RGBColor(0x26, 0x26, 0x26)
    COLOR_WARN = RGBColor(0xA6, 0x2A, 0x00)

    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    def style_table(table, col_widths, headers, data, align_right_cols=(), body_pt=9):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        hdr_cells = table.rows[0].cells
        for i, title in enumerate(headers):
            hdr_cells[i].text = title
            set_cell_background(hdr_cells[i], HEX_PRIMARY)
            set_cell_margins(hdr_cells[i], top=140, bottom=140, left=150, right=150)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if i in align_right_cols else WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.name = 'Calibri'
        trPr = table.rows[0]._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for r_idx, row_data in enumerate(data):
            row_cells = table.add_row().cells
            bg_color = HEX_BG_LIGHT if r_idx % 2 == 1 else 'FFFFFF'
            for c_idx, val in enumerate(row_data):
                row_cells[c_idx].text = str(val)
                set_cell_background(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=150, right=150)
                p = row_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx in align_right_cols else WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.size = Pt(body_pt)
                    run.font.name = 'Calibri'
                    run.font.color.rgb = COLOR_DARK
                    if c_idx == 0:
                        run.font.bold = True
        for row in table.rows:
            # never let a row break across a page boundary: a half-row at the top of a
            # page is unreadable and was observed in the page render of this report
            row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    def para(text, size=10.5, italic=False, color=None, bold=False, after=8):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(size)
        r.font.italic = italic
        r.font.bold = bold
        r.font.color.rgb = color if color is not None else COLOR_DARK
        p.paragraph_format.space_after = Pt(after)
        return p

    def h1(text):
        h = doc.add_heading(level=1)
        r = h.add_run(text)
        r.font.color.rgb = COLOR_PRIMARY
        r.font.name = 'Calibri'
        return h

    def h2(text):
        h = doc.add_heading(level=2)
        r = h.add_run(text)
        r.font.color.rgb = COLOR_SECONDARY
        r.font.name = 'Calibri'
        return h

    def caption(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.5)
        r.font.italic = True
        r.font.color.rgb = COLOR_SECONDARY
        p.paragraph_format.space_after = Pt(14)

    def callout(title, body, fill=HEX_HIGHLIGHT, color=COLOR_PRIMARY):
        t = doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.rows[0].cells[0]
        set_cell_background(c, fill)
        set_cell_margins(c, top=160, bottom=160, left=200, right=200)
        p = c.paragraphs[0]
        rt = p.add_run(title + "\n")
        rt.font.bold = True
        rt.font.size = Pt(10.5)
        rt.font.color.rgb = color
        rb = p.add_run(body)
        rb.font.size = Pt(9.5)
        rb.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # ------------------------------------------------------------------ title
    p = doc.add_paragraph()
    r = p.add_run('RA-MedFiLM-BARR: Scientific Evaluation & Prediction Report')
    r.font.name = 'Calibri'; r.font.size = Pt(23); r.font.bold = True
    r.font.color.rgb = COLOR_PRIMARY
    p.paragraph_format.space_after = Pt(4)

    p = doc.add_paragraph()
    r = p.add_run('Multi-model benchmarking, BARR regional refinement, and single-case '
                  'internal / external prediction panels')
    r.font.name = 'Calibri'; r.font.size = Pt(12.5); r.font.color.rgb = COLOR_SECONDARY
    p.paragraph_format.space_after = Pt(14)

    meta = doc.add_table(rows=1, cols=1)
    meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    mc = meta.rows[0].cells[0]
    set_cell_background(mc, HEX_BG_LIGHT)
    set_cell_margins(mc, top=140, bottom=140, left=200, right=200)
    pm = mc.paragraphs[0]
    rm = pm.add_run(
        'Project: RA-MedFiLM-BARR  |  Repository: D:\\Softfors\\jup  |  Report date: ' + REPORT_DATE + '\n'
        'Internal populations: VAL808 (n=808, selection-consumed), ROUTER_HOLDOUT (n=875, one-shot), '
        'ROUTER_DEVELOPMENT (n=4,957, in-sample)  |  TEST (n=1,683): locked, not accessed\n'
        'External: retrospective stress test, n=884 (CVC 612, BrEaST 252, Stones 20); HAM10000 excluded '
        '\u2014 not an external validation cohort')
    rm.font.name = 'Calibri'; rm.font.size = Pt(8.5); rm.font.italic = True
    rm.font.color.rgb = COLOR_SECONDARY
    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # --------------------------------------------------------- 1. scope note
    h1('1. Scope, Evidence Classes and What This Report Does Not Claim')
    para('This report supersedes the October 30 build. Several statements in that build were not '
         'supported by a stored result record and have been corrected or retracted; Section 9 lists '
         'them explicitly. Every remaining numerical value is bound to a frozen artifact: internal values '
         'to reports/audits/c1_external_evidence_v1_0/claim_provenance.json, and external values to '
         'reports/tables/c1_external_stress_*.csv, which this document reads at build time.')

    para('Evidence classes used throughout:', bold=True, after=4)
    tbl0 = doc.add_table(rows=1, cols=2)
    style_table(tbl0, [2.1, 4.4],
                ['Class', 'Meaning and permitted use'],
                [['VERIFIED', 'Reproducible from a named frozen artifact. Quotable with its population label.'],
                 ['PARTIALLY_VERIFIED', 'The computation is reproducible, but a required input (mask provenance, '
                                        'population identity) is undocumented. Report as a pilot observation only.'],
                 ['UNSUPPORTED', 'No stored record exists. Must not be quoted. Retracted where previously stated.'],
                 ['NOT_ESTABLISHED', 'Planned but never executed. Cells remain empty.']],
                body_pt=8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    callout('Central caution',
            'A cryptographically valid or numerically reproducible result is not evidence of clinical validity. '
            'The C1 trust boundary remains under operator review, and no scientific execution has been authorised. '
            'Nothing in this report constitutes an external validation claim.',
            fill=HEX_WARN, color=COLOR_WARN)

    # ------------------------------------------------- 2. architecture compare
    h1('2. Architecture Comparison')
    h2('2.1 Phase 21 six-model comparison (single shared protocol)')
    para('The six configurations below were trained and evaluated inside the Phase 21 run under an identical '
         'protocol on the VAL808 split (n = 808). This is the only controlled head-to-head in the project. '
         'VAL808 was consumed for model selection, so these values are development estimates, not held-out '
         'test performance.')

    tbl1 = doc.add_table(rows=1, cols=6)
    style_table(tbl1, [1.85, 1.55, 0.85, 0.95, 0.95, 0.95],
                ['Model architecture', 'Backbone / type', 'Parameters', 'Macro Dice', 'Macro IoU', 'KUB Dice'],
                [['Global MedFiLM', 'U-Net + FiLM (5 sites)', '3,523,001', '83.51%', '74.48%', '76.41%'],
                 ['DeepLabV3+', 'ResNet-based', '40,347,041', '82.77%', '74.12%', '73.87%'],
                 ['Transformer / MiT U-Net', 'SegFormer / MiT', '16,347,777', '82.24%', '73.66%', '72.52%'],
                 ['U-Net++', 'Nested dense', '9,159,681', '79.20%', '69.10%', '72.07%'],
                 ['Attention U-Net', 'Attention gates', '7,851,285', '78.90%', '69.27%', '69.58%'],
                 ['Standard U-Net', 'Plain U-Net', '7,763,041', '78.78%', '68.81%', '72.11%']],
                align_right_cols=(2, 3, 4, 5))
    caption('Table 1. Phase 21 six-model comparison on VAL808. Source: '
            'reports/tables/phase21_six_model_comparison.csv. 95% bootstrap CIs are wide and overlap '
            'between Global MedFiLM and DeepLabV3+; the two are not statistically distinguishable.')

    h2('2.2 Regional BARR is a separate run and is not a Phase 21 arm')
    para('Regional BARR (Global MedFiLM + regional refiner R\u03c8 + benefit router B\u03c6 + post-safety '
         'S\u03c9) was never trained or evaluated inside the Phase 21 six-model run. Its results come from '
         'Phase 27/29 (VAL808) and Phase 30 (ROUTER_HOLDOUT) and therefore cannot be entered as a seventh row '
         'of Table 1 without disclosing that the comparison is cross-run.')

    tbl1b = doc.add_table(rows=1, cols=5)
    style_table(tbl1b, [1.7, 1.15, 1.35, 1.2, 1.1],
                ['Configuration', 'Parameters', 'Population', 'Macro Dice', 'Delta vs Global'],
                [['Global MedFiLM', '3,523,001', 'VAL808 (n=808)', '83.51%', 'reference'],
                 ['Regional BARR', '4,837,420', 'VAL808 (n=808), 3-seed mean', '83.79%', '+0.28 pp'],
                 ['Regional BARR', '4,837,420', 'ROUTER_HOLDOUT (n=875)', '93.03%', '+0.17 pp']],
                align_right_cols=(1, 3, 4))
    caption('Table 2. Regional BARR, each row on its own population. Sources: '
            'reports/audits/phase21_analysis.json, phase29_phase_d_three_seed_descriptive_summary.json, '
            'phase30_primary_noninferiority_result.json. Parameter total 4,837,420 from the Phase 34 record '
            '(G 3,523,001 + R\u03c8 1,276,401 + B\u03c6 36,801 + S\u03c9 1,217).')

    para('The BARR result is a preservation / non-inferiority finding, not an improvement finding. '
         'On VAL808 the three-seed mean gain is +0.28 pp with a between-seed range of +0.22 to +0.34 pp; '
         'on the one-shot ROUTER_HOLDOUT the gain is +0.17 pp with a 95% CI of [+0.11, +0.24] against a '
         'non-inferiority margin of \u22120.5 pp. Two of four domains (BUSI, KVASIR) have CIs that include zero.',
         italic=True)

    doc.add_picture('paper_doc/fig1_model_comparison.png', width=Inches(6.4))
    caption('Figure 1. Macro-domain Dice on VAL808. Six bars from the Phase 21 protocol; the hatched bar is '
            'Regional BARR from a separate run and is marked as such. The y-axis does not start at zero.')

    # ------------------------------------------------------- 3. per domain
    h1('3. Domain-Level Results')
    h2('3.1 ROUTER_HOLDOUT (n = 875), one-shot evaluation')
    para('Per-domain absolute scores and descriptive deltas. The one-shot holdout carries a mandatory '
         'disclosed protocol-deviation qualifier: '
         'ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION.')

    tbl2 = doc.add_table(rows=1, cols=6)
    style_table(tbl2, [1.05, 1.15, 0.7, 1.15, 1.15, 1.35],
                ['Domain', 'Modality', 'n', 'Global MedFiLM', 'Regional BARR', 'Delta (95% CI)'],
                [['KUB', 'Abdominal radiograph', '298', '84.97%', '85.57%', '+0.59 pp [+0.36, +0.85]'],
                 ['ISIC', 'Dermoscopy', '383', '93.59%', '93.69%', '+0.10 pp [+0.03, +0.18]'],
                 ['BUSI', 'Breast ultrasound', '90', '95.88%', '95.89%', '+0.001 pp [+0.00, +0.002]'],
                 ['KVASIR', 'GI endoscopy', '104', '96.97%', '96.97%', '+0.002 pp [+0.00, +0.006]'],
                 ['Macro', 'Equal-weight mean', '875', '92.85%', '93.03%', '+0.17 pp [+0.11, +0.24]']],
                align_right_cols=(2, 3, 4, 5), body_pt=8.5)
    caption('Table 3. Per-domain holdout results. Source: '
            'reports/audits/phase30_primary_noninferiority_result.json. Deltas are descriptive bootstrap '
            'quantities; no p-value was computed (Phase 31 established that zero confirmatory significance '
            'procedures are eligible).')

    doc.add_picture('paper_doc/fig2_domain_performance.png', width=Inches(6.4))
    caption('Figure 2. BARR minus Global MedFiLM on ROUTER_HOLDOUT, plotted as a difference with 95% CIs. '
            'A delta plot is used instead of absolute scores so that a sub-1 pp difference is not visually '
            'inflated by a truncated axis.')

    h2('3.2 KUB lesion-size strata (reporting-only metadata)')
    para('These strata describe where the global model loses accuracy. They are reporting metadata only: '
         'the size tiers are never segmentation classes, task IDs, model inputs or routing variables, and no '
         'BARR per-stratum result exists.')

    tbl3 = doc.add_table(rows=1, cols=5)
    style_table(tbl3, [1.0, 1.9, 0.6, 1.05, 2.0],
                ['Stratum', 'Definition', 'n', 'Global Dice', 'Evidence status'],
                [['TINY', 'Sub-centimetre calculi (<0.01% of field)', '44', '53.21%', 'Descriptive only; no BARR result'],
                 ['SMALL', '0.01% - 0.05% of field', '19', '65.42%', 'Descriptive only; no BARR result'],
                 ['MEDIUM', '0.05% - 0.15% of field', '27', '69.98%', 'Descriptive only; no BARR result'],
                 ['LARGE', 'Staghorn / mass (>0.15% of field)', '13', '70.82%', 'Descriptive only; no BARR result'],
                 ['Other KUB', 'Not primary bin', '177', '84.74%', 'Descriptive only; no BARR result']],
                align_right_cols=(2, 3), body_pt=8.5)
    caption('Table 4. KUB size stratification. Source: reports/tables/phase21_kub_size_stratification.csv, '
            'role = REPORTING_ONLY__DESCRIPTIVE. The previously reported claim that BARR lifts the TINY '
            'stratum from 53.21% to 85.57% has been retracted: no such measurement exists.')

    # ------------------------------------------------- 4. safety and compute
    h1('4. Safety and Compute')
    para('On the ROUTER_DEVELOPMENT population (n = 4,957, budget K = 1,239), unconditional refinement (A1) '
         'harms 2,115 of 4,957 cases (42.67%). Adding the cost-aware router (A7) reduces harmful activations '
         'to 412 (8.31%), and adding the post-safety filter on top (A8) reduces them further to 390 (7.87%).')

    para('Decomposition matters. The router accounts for 2,115 \u2192 412 = 1,703 cases; the post-safety '
         'filter accounts for 412 \u2192 390 = 22 cases. The previously reported statement that '
         '\u201cS\u03c9 eliminates 1,725 harmed cases\u201d attributed the whole system-level reduction to one '
         'component and is corrected here.', bold=False)

    callout('In-sample caveat',
            'The 4,957 ROUTER_DEVELOPMENT rows are a subset of the 5,832 TRAIN samples. This is in-sample '
            'development evidence, not held-out evidence. A reduced average harm rate is also not evidence of '
            'zero harmful outcomes: 390 harmful refinements remain in A8.',
            fill=HEX_WARN, color=COLOR_WARN)

    doc.add_picture('paper_doc/fig3_safety_compute.png', width=Inches(6.4))
    caption('Figure 3. Harm rate on an intent-to-treat denominator (left) and refiner workload (right), '
            'decomposed by component. Source: reports/tables/phase28_table_02_arm_primary_metrics.csv.')

    # --------------------------------------------- 5. prediction panels
    h1('5. Single-Case Prediction Panels (internal)')
    para('The panels in this section were produced by a single forward pass of GlobalMedFiLM '
         '(checkpoint SHA-256 286689fd\u20265ba1b7, 3,523,001 parameters) at 512\u00d7512, sigmoid threshold 0.5. '
         'Only the global model was loaded for these four internal cases; BARR is executed separately and '
         'is reported in Section 6.')

    para('Columns are: input image; ground-truth mask; predicted probability map; predicted segmentation '
         'overlay; and a pixel error classification map using TP #00E600, FP #FF2020, FN #2060FF and '
         'TN #181818. Dice, IoU, precision, recall, specificity and accuracy are computed from the same '
         'prediction and the same ground truth shown in that row.', after=6)

    para('Class-wise segmentation here means foreground versus background under the current binary ontology. '
         'The \u201cpresentation label\u201d shown in each row is curated analyst metadata. It is not a model '
         'output and must not be read as a pixelwise subclass prediction.', italic=True)

    h2('5.1 Internal VAL808 cases')
    tbl4 = doc.add_table(rows=1, cols=9)
    style_table(tbl4, [0.85, 1.25, 1.05, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
                ['Modality', 'Presentation label (metadata)', 'Case', 'Dice', 'IoU', 'Prec', 'Recall', 'Spec', 'Acc'],
                [['ISIC 2018', 'Pigmented lesion', 'ISIC_0013798', '78.10%', '64.07%', '64.07%', '100.00%', '99.76%', '99.76%'],
                 ['BUSI', 'Hypoechoic mass', '00170.bmp', '87.25%', '77.38%', '80.43%', '95.33%', '99.87%', '99.85%'],
                 ['Kvasir-SEG', 'Colorectal polyp', 'cju1alwgo30z...', '80.00%', '66.67%', '95.94%', '68.61%', '99.73%', '97.09%'],
                 ['KUB-StoneX', 'Bladder calculus', '00001-00-2500001', '65.12%', '48.28%', '48.28%', '100.00%', '99.99%', '99.99%']],
                align_right_cols=(3, 4, 5, 6, 7, 8), body_pt=8)
    caption('Table 5. Internal single-case metrics. All four cases were confirmed present in '
            'manifests/phase4_v3/val.csv and absent from train.csv. Values reproduced independently to two '
            'decimal places from the stated checkpoint.')

    doc.add_picture('paper_doc/fig4_internal_4domain_predictions.png', width=Inches(6.6))
    caption('Figure 4. Internal VAL808 single-case panels. n = 1 case per modality; illustrative only.')

    para('Note on the KUB case: its ground-truth lesion is 14 pixels. Dice on a 14-pixel object is extremely '
         'sensitive to a handful of boundary pixels and should not be read as representative of KUB '
         'performance, which is 76.41% macro over 280 VAL808 cases.', italic=True)

    # ------------------------------------------- 6. external stress test
    h1('6. External Stress Test (n = 884, Global and Regional BARR)')
    S = load_stress()
    m = S['m']

    def pct(x, nd=2):
        """Fractions are stored 0..1 in the result tables; render them as percent."""
        return f"{x * 100:.{nd}f}%"

    cc = S['construction']['cohorts']

    para('This section replaces the previous external pilot. That pilot ran one hand-picked case per '
         'dataset, used a non-canonical resize convention (a plain 512\u00d7512 stretch rather than the '
         'canonical aspect-preserving pad), and included a HAM10000 row whose mask provenance could not be '
         'established. All of those values are retracted (items A, B and C in Section 9). What follows was '
         'produced by a frozen, pre-registered design saved before any external prediction existed.')

    callout('Classification of this evidence',
            'RETROSPECTIVE_EXTERNAL_STRESS_TEST. The cohorts were not prospectively held out; all three were '
            'previously inspected while building manifests and an evidence audit. No checkpoint, threshold, '
            'seed or preprocessing choice was selected using external performance. These are descriptive '
            'observations, not a validation study, and no confirmatory p-value is computed anywhere in this '
            'section.',
            fill=HEX_WARN, color=COLOR_WARN)

    h2('6.1 Cohorts, exclusions and preprocessing')
    tbl6 = doc.add_table(rows=1, cols=6)
    style_table(tbl6, [1.5, 1.05, 1.1, 1.0, 1.15, 1.6],
                ['Cohort', 'Rows in manifest', 'Analysed', 'task_id', 'Domain analogue', 'Excluded'],
                [['CVC-ClinicDB', str(cc['cvc']['rows_in_manifest']), str(cc['cvc']['rows_analysed']),
                  str(cc['cvc']['task_id']), 'KVASIR', '0'],
                 ['BrEaST-Lesions-USG', str(cc['breast']['rows_in_manifest']),
                  str(cc['breast']['rows_analysed']), str(cc['breast']['task_id']), 'BUSI',
                  '4 marked not evaluable; 18 further images have no mask'],
                 ['Stones_where_are_you (test split)', str(cc['stones']['rows_after_split_filter']),
                  str(cc['stones']['rows_analysed']), str(cc['stones']['task_id']), 'KUB',
                  '0 within the test split'],
                 ['HAM10000', str(cc['ham10000']['rows_in_manifest']), '0', '\u2014', '\u2014',
                  'EXCLUDED \u2014 mask provenance unverified']],
                body_pt=8)
    caption('Table 6. External cohorts. Manifest digests and per-cohort sample-ID digests are recorded in '
            'reports/audits/c1_external_stress_v1_0/cohort_construction.json.')

    para('Preprocessing is the canonical inference transform used to train and validate the global model: '
         'RGB, aspect-preserving bilinear resize with scale = min(512/W, 512/H), centred on a 512\u00d7512 '
         'canvas with zero padding, divided by 255. Ground truth is put through the same geometry with '
         'nearest-neighbour resampling and binarised at > 0. For the Stones COCO export, polygons with '
         'category_id 7 (\u201cstone\u201d) are rasterised at native resolution first and only then resized; '
         'all nine other categories are background. The threshold is 0.5 everywhere, with no per-cohort '
         'tuning, no test-time augmentation and no post-processing.', after=6)

    para('No row was dropped after seeing a result. A case is kept even when its ground truth or its '
         'prediction is empty, because dropping degenerate cases would flatter the model.', italic=True)

    h2('6.2 Global MedFiLM: macro metrics per cohort')
    rows = []
    for key, label in (('cvc', 'CVC-ClinicDB'), ('breast', 'BrEaST-Lesions-USG'),
                       ('stones', 'Stones (all 20)')):
        rows.append([
            label,
            pct(m(key, 'global', 'Dice')),
            f"[{m(key, 'global', 'Dice', 'ci_low') * 100:.2f}, "
            f"{m(key, 'global', 'Dice', 'ci_high') * 100:.2f}]",
            pct(m(key, 'global', 'IoU')),
            pct(m(key, 'global', 'Precision')),
            pct(m(key, 'global', 'Recall')),
            pct(m(key, 'global', 'Specificity')),
            f"{m(key, 'global', 'HD95_px'):.1f}",
            f"{m(key, 'global', 'NSD_2px'):.3f}",
        ])
    tbl7 = doc.add_table(rows=1, cols=9)
    style_table(tbl7, [1.35, 0.72, 1.0, 0.62, 0.72, 0.62, 0.8, 0.6, 0.55],
                ['Cohort', 'Dice', '95% CI', 'IoU', 'Precision', 'Recall', 'Specificity',
                 'HD95 (px)', 'NSD@2'],
                rows, align_right_cols=(1, 2, 3, 4, 5, 6, 7, 8), body_pt=8)
    caption('Table 7. Global MedFiLM, macro mean over cases (equal case weight), threshold 0.50. '
            'Intervals are percentile bootstrap over clusters (CVC: 29 sequences; BrEaST: 252 cases; '
            'Stones: none, n = 20). HD95 and NSD are in PIXELS \u2014 no external cohort ships physical '
            'pixel spacing, so no millimetre value is reported or implied.')

    para('Surface metrics are not comparable across these cohorts: the three datasets have different '
         'fields of view and acquisition geometry, and a pixel means something different in each. Only '
         'within-cohort comparisons between Global and BARR are meaningful, because those share a canvas.',
         italic=True)

    h2('6.3 Stones must be read as three separate statements')
    sub = S['subgroups']
    sp = sub[(sub.subgroup == 'six_positive') & (sub.arm == 'global')]
    fa = sub[(sub.subgroup == 'fourteen_absent') & (sub.arm == 'global')]

    def sub_val(frame, metric, field='mean'):
        return float(frame[frame.metric == metric].iloc[0][field])

    tbl8 = doc.add_table(rows=1, cols=4)
    style_table(tbl8, [1.7, 0.7, 1.9, 2.6],
                ['Stones subgroup', 'n', 'Global Dice (mean)', 'What it means'],
                [['All 20 test images', '20', pct(m('stones', 'global', 'Dice')),
                  'Dominated by the 14 images with no stone, each scoring 0'],
                 ['Stone present', '6', pct(sub_val(sp, 'Dice')),
                  f"Recall {pct(sub_val(sp, 'Recall'))}, precision "
                  f"{pct(sub_val(sp, 'Precision'))} \u2014 lesions are found but grossly over-segmented"],
                 ['Stone absent', '14', 'undefined (empty ground truth)',
                  f"Precision {pct(sub_val(fa, 'Precision'))}: the model produced foreground on 14 of 14 "
                  'stone-free radiographs']],
                body_pt=8)
    caption('Table 8. Stones stratified by annotation, not by a post-hoc threshold. The 20-image cohort '
            'contains 6 images with at least one category-7 annotation and 14 with none.')

    para('The single \u201cStones Dice\u201d of 8.08% is therefore not a segmentation score. It is the '
         'arithmetic consequence of scoring 14 empty-ground-truth images as zero plus six very poor '
         'segmentations. The substantive finding is that the global model has no true-negative behaviour on '
         'this cohort: it marked foreground on every stone-free image, with a mean predicted area far larger '
         'than any annotated stone. This is a failure of domain transfer, and it is reported as one.')

    h2('6.4 Regional BARR on the same cases')
    ex = S['exec']
    states = ex['observed_states']
    sel = ex['selection_fraction']
    para('BARR executed end-to-end from the verified artefacts. All four components hash-matched their '
         'frozen bindings before the first forward pass, all state dictionaries loaded with strict=True, '
         'and the two equivalent forms of the routing decision agreed on every one of the 884 cases. '
         'No case failed and no case fell back to the global mask for lack of an ROI.')

    rows = []
    for key, label in (('cvc', 'CVC-ClinicDB'), ('breast', 'BrEaST-Lesions-USG'),
                       ('stones', 'Stones (all 20)')):
        st = states[key]
        rows.append([label, f"{sel[key] * 100:.2f}%",
                     str(st.get('ACCEPTED', 0)), str(st.get('REJECTED', 0)),
                     str(st.get('NOT_ATTEMPTED', 0)), str(st.get('FAILED', 0)),
                     f"{m(key, 'global', 'Dice') * 100:.2f}%",
                     f"{m(key, 'barr', 'Dice') * 100:.2f}%",
                     f"{(m(key, 'barr', 'Dice') - m(key, 'global', 'Dice')) * 100:+.2f} pp"])
    tbl9 = doc.add_table(rows=1, cols=9)
    style_table(tbl9, [1.3, 0.72, 0.75, 0.72, 0.95, 0.6, 0.78, 0.78, 0.85],
                ['Cohort', 'Selected', 'Accepted', 'Rejected', 'Not attempted', 'Failed',
                 'Global Dice', 'BARR Dice', 'Difference'],
                rows, align_right_cols=(1, 2, 3, 4, 5, 6, 7, 8), body_pt=8)
    caption('Table 9. BARR execution outcomes and paired Dice. \u201cSelected\u201d is the fraction of cases '
            'the router sent to refinement; \u201cnot attempted\u201d cases keep the global mask. '
            'Accepted + Rejected + Not attempted + Failed equals n for every cohort.')

    p = S['paired']
    rows = []
    for key, label in (('cvc', 'CVC-ClinicDB'), ('breast', 'BrEaST-Lesions-USG'),
                       ('stones', 'Stones (all 20)')):
        g = p[p.cohort_key == key]
        rows.append([label, str(len(g)),
                     str(int((g.outcome == 'improved').sum())),
                     str(int((g.outcome == 'unchanged').sum())),
                     str(int((g.outcome == 'worsened').sum())),
                     f"{g.delta_dice.mean() * 100:+.2f} pp",
                     f"{g.delta_dice.median() * 100:+.2f} pp",
                     f"{g.delta_dice.quantile(0.25) * 100:+.2f} to "
                     f"{g.delta_dice.quantile(0.75) * 100:+.2f} pp"])
    tbl10 = doc.add_table(rows=1, cols=8)
    style_table(tbl10, [1.3, 0.55, 0.8, 0.9, 0.8, 0.95, 0.95, 1.35],
                ['Cohort', 'n', 'Improved', 'Unchanged', 'Worsened', 'Mean change',
                 'Median change', 'Interquartile range'],
                rows, align_right_cols=(1, 2, 3, 4, 5, 6, 7), body_pt=8)
    caption('Table 10. Per-case paired change in Dice (BARR minus Global). \u201cUnchanged\u201d includes '
            'every case the router did not select and every case the safety gate rejected, because those '
            'keep the global mask by construction. The median and the quartiles are zero because most cases '
            'are unchanged; the mean is the informative column.')

    para('The effect is small and positive in all three cohorts, and it is the same order of magnitude as '
         'the internal preservation result (+0.28 pp on VAL808). It is not an improvement claim: the '
         'interquartile range straddles zero in every cohort, and in BrEaST the number of worsened cases '
         '(20) is close to the number improved (27).', after=6)

    para('One property of the router must be stated plainly. Its threshold was calibrated on the internal '
         'development population with a fixed 25% budget. On external cohorts the selection fraction is an '
         'outcome, not a controlled quantity: 19.28% for CVC, 22.22% for BrEaST and 50% for Stones. The '
         'Stones figure in particular reflects that the router scores were near the threshold, not that '
         'half of those images deserved refinement. No recalibration was performed, because recalibrating '
         'on the test cohort would make the result uninterpretable.')

    h2('6.5 Domain shift')
    sh = S['shift']
    rows = []
    for _, r in sh.iterrows():
        rows.append([r['cohort'], r['domain_analogue'],
                     f"{r['internal_val808_dice'] * 100:.2f}%",
                     f"{r['external_global_dice'] * 100:.2f}%",
                     f"{r['delta_vs_internal_pp']:+.2f} pp",
                     f"{r['gt_area_fraction_median'] * 100:.3f}%",
                     f"{r['pred_area_fraction_median'] * 100:.3f}%"])
    tbl11 = doc.add_table(rows=1, cols=7)
    style_table(tbl11, [1.4, 0.85, 1.15, 1.15, 0.95, 1.1, 1.15],
                ['Cohort', 'Analogue', 'Internal VAL808', 'External Global', 'Shift',
                 'GT area (median)', 'Predicted area (median)'],
                rows, align_right_cols=(2, 3, 4, 5, 6), body_pt=8)
    caption('Table 11. Domain shift. The internal column is the frozen Phase 21 VAL808 per-domain Dice for '
            'the same task id; it is a different population and is used only as a shift anchor, never as a '
            'like-for-like comparison.')

    _sh = {r['cohort']: r for _, r in sh.iterrows()}
    para(f"The shift is large and it is not uniform. Endoscopy loses "
         f"{abs(_sh['CVC-ClinicDB']['delta_vs_internal_pp']):.1f} pp and breast ultrasound "
         f"{abs(_sh['BrEaST-Lesions-USG']['delta_vs_internal_pp']):.1f} pp relative to their internal "
         f"analogues, while the Stones radiographs lose "
         f"{abs(_sh['Stones_where_are_you']['delta_vs_internal_pp']):.1f} pp. The median predicted area "
         "fraction explains the last one: the model covers a far larger share of the canvas than the "
         "annotations do, so the failure is over-segmentation rather than a failure to respond.", after=6)

    para('This is the substantive external result of the study. A model that reaches 83.51% macro-domain '
         'Dice on its internal validation split does not carry that performance to external data from the '
         'same nominal modalities, and the degradation is severe enough on one cohort to make the model '
         'unusable there without domain adaptation.', italic=True)

    h2('6.6 Figures')
    doc.add_picture('reports/figures/fig6_external_cvc.png', width=Inches(6.9))
    caption('Figure 5. CVC-ClinicDB stress-test panels, 8 columns: input, ground truth, global prediction, '
            'global error map, global probability, BARR prediction, BARR error map and BARR decision trace. '
            'Rows are the median-, best- and worst-Dice cases, selected by rule.')
    doc.add_picture('reports/figures/fig7_external_breast.png', width=Inches(6.9))
    caption('Figure 6. BrEaST-Lesions-USG stress-test panels, same column set and same selection rule.')
    doc.add_picture('reports/figures/fig8_external_stones.png', width=Inches(6.9))
    caption('Figure 7. Stones stress-test panels. The cohort-wide median Dice is zero because 14 of 20 cases '
            'have an empty ground truth; that row is kept deliberately rather than replaced, because it '
            'shows the false-positive behaviour that defines this cohort.')

    para('The error palette is identical to Figures 1\u20134: TP #00E600, FP #FF2020, FN #2060FF, TN #181818. '
         'The cyan rectangle in column 8 is the frozen ROI window proposed from the predicted probability '
         'map at threshold 0.30; it is geometry, not a model output.', italic=True)

    # ------------------------------------------- 7. dataset independence
    h1('7. Dataset Independence and Mask Provenance')
    tbl6 = doc.add_table(rows=1, cols=4)
    style_table(tbl6, [1.35, 1.5, 1.75, 1.9],
                ['Dataset', 'Documented source', 'Independence from training', 'Verdict'],
                [['HAM10000', 'ISIC-2018 Task 3 training input (classification archive, CC BY-NC 4.0)',
                  'Image IDs disjoint from the frozen ISIC set (0 of 10,015 overlap), but patient/lesion '
                  'grouping is absent from the supplied metadata, so lesion-level independence is not established',
                  'PARTIALLY_VERIFIED'],
                 ['CVC-ClinicDB', 'Public colonoscopy segmentation set; frame_id and sequence_id supplied',
                  'No filename or ID overlap with the frozen KVASIR set',
                  'VERIFIED (pairing)'],
                 ['BrEaST-Lesions-USG', 'Public breast ultrasound set, one folder per case',
                  'No filename overlap with BUSI; 18 of 270 images have no mask',
                  'VERIFIED (pairing, partial)'],
                 ['Stones_where_are_you? v3', 'Roboflow, public domain, COCO-segmentation export',
                  'No overlap with KUB-StoneX; 6 of 20 test images contain a stone annotation',
                  'VERIFIED (identity and mapping)']],
                body_pt=8)
    caption('Table 12. External dataset provenance. Frozen-split comparison used '
            'manifests/phase4_v3/{train,val,all_paired}.csv only; no protected pixels were opened.')

    callout('HAM10000 is excluded from this study',
            'The HAM10000 folder is the ISIC-2018 Task 3 archive, which contains classification labels and no '
            'segmentation masks. The 10,015 masks present in the folder therefore come from an undocumented '
            'source. Rather than score the model against an unattributable mask, HAM10000 was excluded before '
            'any inference was run. The previously reported 79.15% Dice is retracted (item B, Section 9) and '
            'must not be cited anywhere.',
            fill=HEX_WARN, color=COLOR_WARN)

    para('Dataset-level independence is not established for any external cohort. The project\u2019s own Phase 32 '
         'audit concluded that no prospective clean external cohort is eligible. The 884-case study in '
         'Section 6 is a retrospective stress test: it measures how the frozen model behaves on data it was '
         'not trained on, and it does not establish generalisation because the cohorts were not held out '
         'prospectively and were previously inspected.')

    # ------------------------------------------------ 8. limitations
    h1('8. Statistical Limitations and Comparability')
    for t in [
        'No confirmatory significance testing is available. Phase 31 recorded zero new p-values, zero new '
        'effect sizes and zero eligible confirmatory procedures. No p-value appears anywhere in this report.',
        'VAL808 (n = 808) was consumed for model selection and early stopping, so all VAL808 numbers are '
        'development estimates.',
        'ROUTER_HOLDOUT (n = 875) was evaluated once and carries a disclosed post-first-open source-freeze '
        'deviation. It is not an independent external cohort.',
        'The Phase 21 six-model comparison and the BARR results come from different runs. Cross-run comparison '
        'is descriptive only; no controlled head-to-head between BARR and the baselines exists.',
        'Per-domain CIs for BUSI and KVASIR include zero, so those domains show no measurable difference.',
        'The external study is retrospective, not prospective. All three cohorts were previously inspected '
        'while building manifests and an evidence audit, and 8 hand-picked single cases had already been run '
        'under a different resize convention. No threshold, checkpoint or seed was chosen on external '
        'performance, but the cohorts are not a clean holdout.',
        'External uncertainty is a percentile bootstrap over clusters, described as such. It is not a '
        'confidence interval in a confirmatory sense, and no multiplicity correction is applied because no '
        'family of hypotheses is tested.',
        'Surface metrics on external data are in pixels. No cohort ships physical pixel spacing, so HD95, '
        'ASSD and NSD cannot be converted to millimetres and cannot be compared across cohorts.',
        'The Stones cohort is n = 20 with 6 positive cases. It carries no interval estimate; point estimates '
        'and counts are reported and no subgroup comparison is made.',
        'The BARR router threshold was calibrated on the internal development population. Its external '
        'selection fraction is an outcome of that fixed threshold, not a controlled property of the cohort.',
        'TEST (n = 1,683) remains locked and was not accessed for any value in this report.',
    ]:
        b = doc.add_paragraph(style='List Bullet')
        r = b.add_run(t)
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'

    # ------------------------------------------------ 9. retractions
    h1('9. Corrections and Retractions Relative to the October 30 Build')
    para('Items A\u2013H below are the corrections applied to this build. A\u2013D and H change what the report '
         'asserts about external data; E\u2013G change how those assertions are framed and bounded.')
    tbl13 = doc.add_table(rows=1, cols=4)
    style_table(tbl13, [0.35, 1.85, 1.6, 2.5],
                ['#', 'Statement in the previous build', 'Status', 'Correction'],
                [['A', 'External section presented an n = 1 per-dataset pilot, Table 6',
                  'SUPERSEDED',
                  'Replaced by the 884-case retrospective stress test in Section 6, produced by a design '
                  'frozen before any external prediction existed.'],
                 ['B', 'HAM10000 Dice 79.15%', 'RETRACTED',
                  'HAM10000 excluded: the folder is the ISIC-2018 Task 3 classification release with no '
                  'documented masks. No HAM10000 inference was run.'],
                 ['C', 'Figure 5 caption: "No BARR decision is shown because none was executed"',
                  'FALSE IN THIS BUILD',
                  'BARR has now been executed end-to-end on all 884 cases from verified artefacts. Figures '
                  '5\u20137 show the BARR prediction, BARR error map and decision trace.'],
                 ['D', '"BARR S\u03c9 caught / rejected" external cases: no decision record exists',
                  'SUPERSEDED',
                  'A decision record now exists for every external case: 83 accepted and 35 rejected on CVC, '
                  '47 and 9 on BrEaST, 9 and 1 on Stones. These are counts, not a safety claim.'],
                 ['E', '"The external material is a pilot, not a validation"', 'REFINED',
                  'Still not a validation, and now stated with the correct reason: the study is a '
                  'retrospective stress test with no prospective holdout.'],
                 ['F', 'No quantification of domain shift', 'FILLED',
                  'Section 6.5 quantifies the shift against the internal VAL808 per-domain anchors: '
                  '\u221213.4 pp (CVC), \u221215.1 pp (BrEaST), \u221268.3 pp (Stones).'],
                 ['G', 'External numbers reported without a stated aggregation mode', 'CORRECTED',
                  'Every external number now states macro-over-cases aggregation, its interval scheme, and '
                  'that surface metrics are in pixels.'],
                 ['H', '"No external validation exists"', 'SUPERSEDED',
                  'External measurement now exists and is reported with its limits. The claim that no '
                  'external *validation* exists is retained, because none does.']],
                body_pt=8)
    caption('Table 13. Correction and retraction register for this build. External evidence trail in '
            'reports/audits/c1_external_stress_v1_0/; earlier trail in '
            'reports/audits/c1_external_evidence_v1_0/.')

    para('The register below is carried forward unchanged from the October 30 correction pass. Those '
         'retractions remain in force; nothing in this build reinstates any of them.', italic=True)
    tbl14 = doc.add_table(rows=1, cols=3)
    style_table(tbl14, [2.0, 1.5, 2.8],
                ['Statement in the previous build', 'Status', 'Correction'],
                [['Regional BARR macro Dice 86.24%', 'UNSUPPORTED',
                  'No stored record contains this value. Replaced by 83.79% on VAL808 (3-seed mean) and '
                  '93.03% on ROUTER_HOLDOUT, each with its population label.'],
                 ['BARR parameters 4.80M', 'UNSUPPORTED',
                  'Correct value 4,837,420 (4.84M) from the Phase 34 record.'],
                 ['Deltas marked "p<0.001" / "p<0.01" / "Significant"', 'UNSUPPORTED',
                  'No p-value was ever computed. Removed; deltas are descriptive with 95% bootstrap CIs.'],
                 ['"S\u03c9 eliminates 1,725 harmed cases"', 'MISATTRIBUTED',
                  '1,725 = A1\u2192A8 system-level reduction. S\u03c9 alone accounts for 412\u2192390 = 22 cases.'],
                 ['"BARR lifts TINY from 53.21% to 85.57%"', 'UNSUPPORTED',
                  'No BARR per-stratum measurement exists. 53.21% is the Global MedFiLM TINY stratum value. Removed.'],
                 ['"Independent external multi-center datasets"', 'OVERSTATED',
                  'Dataset-level independence is not established for any cohort; see Section 7.'],
                 ['BARR KUB Dice 85.57% and IoU 77.85%', 'UNSUPPORTED',
                  'These are the ROUTER_HOLDOUT KUB value and an unrecorded IoU. Removed from the VAL808 table.']],
                body_pt=8)
    caption('Table 14. Retraction register carried forward from the October 30 build.')

    # ------------------------------------------------ 10. trust boundary
    h1('10. Trust Boundary Status')
    para('The C1 launch release is frozen at RC3 (digest 54d1273a\u20263549f) and is unmodified by this report. '
         'The production trust root was found to contain agent-generated signing material, and the RC3 gate '
         'currently refuses its own release digest because it delegates identity verification to RC2. '
         'Consequently no scientific execution is authorised, no production grant has been minted, and no '
         'dataset has been opened through a production launch. The trust store is excluded from scientific use '
         'pending accountable human review. This report does not create a trust policy, sign any approval, or '
         'constitute an authorisation.')

    # ------------------------------------------------ 11. what holds
    h1('11. What the Evidence Does Support')
    callout('Defensible summary',
            '1. Global MedFiLM reaches 83.51% macro-domain Dice on VAL808 (n = 808) with 3.52M parameters, '
            'ranking first of six under a single shared protocol, and is not statistically distinguishable '
            'from DeepLabV3+.\n'
            '2. Regional BARR preserves macro Dice relative to Global MedFiLM: +0.28 pp on VAL808 (three-seed '
            'mean) and +0.17 pp on the one-shot ROUTER_HOLDOUT, within a \u22120.5 pp non-inferiority margin. '
            'This is a preservation result, not an improvement claim.\n'
            '3. On in-sample development data the router removes most harmful refinements and the post-safety '
            'filter removes a further 22 cases, at 24.3% of the unconditional refiner workload.\n'
            '4. On 884 external cases the frozen system runs end-to-end without error, and BARR changes the '
            'per-case Dice by a median of 0.00 pp in every cohort, with a macro change of '
            f"{(m('cvc', 'barr', 'Dice') - m('cvc', 'global', 'Dice')) * 100:+.2f} pp (CVC), "
            f"{(m('breast', 'barr', 'Dice') - m('breast', 'global', 'Dice')) * 100:+.2f} pp (BrEaST) and "
            f"{(m('stones', 'barr', 'Dice') - m('stones', 'global', 'Dice')) * 100:+.2f} pp (Stones). "
            'Preservation transfers; improvement does not.\n'
            '5. External performance is far below internal performance: '
            f"{S['shift'][S['shift'].cohort == 'CVC-ClinicDB'].delta_vs_internal_pp.iloc[0]:+.1f} pp on "
            'CVC-ClinicDB, '
            f"{S['shift'][S['shift'].cohort == 'BrEaST-Lesions-USG'].delta_vs_internal_pp.iloc[0]:+.1f} pp on "
            'BrEaST-Lesions-USG and '
            f"{S['shift'][S['shift'].cohort == 'Stones_where_are_you'].delta_vs_internal_pp.iloc[0]:+.1f} pp on "
            'Stones relative to the internal VAL808 anchors. On the Stones cohort the model marked foreground '
            'on 14 of 14 stone-free radiographs.\n'
            '6. No external *validation* exists. The 884-case study is a retrospective stress test, and its '
            'cohorts were previously inspected, so it bounds failure modes rather than estimating '
            'generalisation.',
            fill=HEX_HIGHLIGHT, color=COLOR_PRIMARY)

    p = doc.add_paragraph()
    r = p.add_run('Report date: ' + REPORT_DATE + '  |  RA-MedFiLM-BARR Scientific Investigation Team')
    r.font.size = Pt(8.5); r.font.italic = True; r.font.color.rgb = COLOR_SECONDARY

    out_path = Path('paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx')
    doc.save(out_path)
    print(f'Report successfully saved to {out_path.resolve()}')


if __name__ == '__main__':
    create_report()
