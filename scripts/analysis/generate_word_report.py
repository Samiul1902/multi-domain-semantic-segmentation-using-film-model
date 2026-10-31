"""Build paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx.

Every number in this report is bound to a frozen artifact. The binding table is
reports/audits/c1_external_evidence_v1_0/claim_provenance.json and is enforced by
tests/test_c1_external_evidence.py.

Corrections relative to the previous build of this report:
  * Regional BARR macro Dice was stated as 86.24 % with no supporting record.
    It is replaced by the Phase 29 three-seed mean on VAL808 (83.79 %) and the
    Phase 30 ROUTER_HOLDOUT value (93.03 %), each labelled with its population.
  * BARR parameter count 4.80 M -> 4,837,420 (4.84 M), from the Phase 34 record.
  * Fabricated p-values ("p<0.001", "p<0.01", "Significant") removed. Phase 31
    established that no confirmatory significance procedure is eligible.
  * "BARR S_omega triggered" / "caught by BARR" assertions removed: no BARR
    route decision exists for any external case.
  * External pilot is presented as n = 1 case per dataset, Global FiLM only,
    explicitly not an external validation cohort.
"""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from pathlib import Path

REPORT_DATE = "October 31, 2026"


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
        'External: single-case pilot only (n=1 per dataset) \u2014 not an external validation cohort')
    rm.font.name = 'Calibri'; rm.font.size = Pt(8.5); rm.font.italic = True
    rm.font.color.rgb = COLOR_SECONDARY
    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # --------------------------------------------------------- 1. scope note
    h1('1. Scope, Evidence Classes and What This Report Does Not Claim')
    para('This report supersedes the October 30 build. Several statements in that build were not '
         'supported by a stored result record and have been corrected or retracted; Section 8 lists '
         'them explicitly. Every remaining numerical value is bound to a frozen artifact in '
         'reports/audits/c1_external_evidence_v1_0/claim_provenance.json.')

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
    h1('5. Single-Case Prediction Panels')
    para('Both panels were produced by a single forward pass of GlobalMedFiLM '
         '(checkpoint SHA-256 286689fd\u20265ba1b7, 3,523,001 parameters) at 512\u00d7512, sigmoid threshold 0.5. '
         'The BARR components were not loaded, so no panel shows a routing, refinement or safety decision.')

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

    h2('5.2 External pilot cases')
    para('The external datasets were obtained and inspected by the researcher. Exactly one case per dataset '
         'was run. These are illustrative single cases and are not a dataset-level external evaluation.')

    tbl5 = doc.add_table(rows=1, cols=10)
    style_table(tbl5, [0.95, 1.15, 0.95, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.6],
                ['Dataset', 'Presentation label (metadata)', 'Case', 'Dice', 'IoU', 'Prec', 'Recall', 'Spec', 'Acc', 'Status'],
                [['HAM10000', 'Melanocytic naevus (NV)', 'ISIC_0024306', '79.15%', '65.50%', '100.00%', '65.50%', '100.00%', '88.17%', 'Partial'],
                 ['CVC-ClinicDB', 'Colonic polyp (frame 1)', '1.png', '42.69%', '27.14%', '97.02%', '27.37%', '99.85%', '88.69%', 'Verified'],
                 ['BrEaST-USG', 'Breast lesion (case 001)', 'case001.png', '18.86%', '10.41%', '16.53%', '21.94%', '91.04%', '85.87%', 'Verified'],
                 ['Stones v3', 'Radio-opaque calculus', '1_png.rf.abc...', '5.65%', '2.91%', '2.91%', '100.00%', '89.00%', '89.03%', 'Verified']],
                align_right_cols=(3, 4, 5, 6, 7, 8), body_pt=8)
    caption('Table 6. External single-case metrics, n = 1 per dataset, Global FiLM only. '
            '\u201cPartial\u201d marks HAM10000: the mask has undocumented provenance (see Section 6).')

    doc.add_picture('paper_doc/fig5_external_4domain_predictions.png', width=Inches(6.6))
    caption('Figure 5. External pilot single-case panels. No BARR decision is shown because none was executed.')

    para('Two failure patterns are visible and are reported descriptively: the endoscopy and dermoscopy cases '
         'under-segment (recall 27.37% and 65.50% respectively, high precision), while the ultrasound and '
         'radiograph cases over-segment (precision 16.53% and 2.91%, recall near 100%). These are observations '
         'about four images, not a characterisation of the datasets.', italic=True)

    # ------------------------------------------- 6. dataset independence
    h1('6. Dataset Independence and Mask Provenance')
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
    caption('Table 7. External dataset provenance. Frozen-split comparison used '
            'manifests/phase4_v3/{train,val,all_paired}.csv only; no protected pixels were opened.')

    callout('HAM10000 mask provenance is unresolved',
            'The HAM10000 folder is the ISIC-2018 Task 3 archive, which contains classification labels and no '
            'segmentation masks. The 10,015 masks present in the folder therefore come from an undocumented '
            'source. The Dice in Table 6 for that case is a correct computation against the mask on disk, but '
            'that mask is not a documented ground truth, so the value is classified PARTIALLY_VERIFIED and must '
            'not be cited as an external segmentation score.',
            fill=HEX_WARN, color=COLOR_WARN)

    para('Dataset-level independence is not established for any external dataset. The project\u2019s own Phase 32 '
         'audit concluded that no prospective clean external cohort is eligible and that external validation '
         'was not performed. The external material in this report is therefore a pilot, not a validation.')

    # ------------------------------------------------ 7. limitations
    h1('7. Statistical Limitations and Comparability')
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
        'The external pilot is n = 1 per dataset. Single-case metrics have no sampling distribution and cannot '
        'be aggregated into a dataset score.',
        'TEST (n = 1,683) remains locked and was not accessed for any value in this report.',
    ]:
        b = doc.add_paragraph(style='List Bullet')
        r = b.add_run(t)
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'

    # ------------------------------------------------ 8. retractions
    h1('8. Corrections and Retractions Relative to the October 30 Build')
    tbl7 = doc.add_table(rows=1, cols=3)
    style_table(tbl7, [2.0, 2.1, 2.4],
                ['Statement in the previous build', 'Status', 'Correction'],
                [['Regional BARR macro Dice 86.24%', 'UNSUPPORTED',
                  'No stored record contains this value. Replaced by 83.79% on VAL808 (3-seed mean) and '
                  '93.03% on ROUTER_HOLDOUT, each with its population label.'],
                 ['BARR parameters 4.80M', 'UNSUPPORTED', 'Correct value 4,837,420 (4.84M) from the Phase 34 record.'],
                 ['Deltas marked "p<0.001" / "p<0.01" / "Significant"', 'UNSUPPORTED',
                  'No p-value was ever computed. Removed; deltas are descriptive with 95% bootstrap CIs.'],
                 ['"BARR S\u03c9 caught / rejected" external cases', 'UNSUPPORTED',
                  'Only Global MedFiLM was executed on external data. No BARR decision record exists. Removed.'],
                 ['"S\u03c9 eliminates 1,725 harmed cases"', 'MISATTRIBUTED',
                  '1,725 = A1\u2192A8 system-level reduction. S\u03c9 alone accounts for 412\u2192390 = 22 cases.'],
                 ['"BARR lifts TINY from 53.21% to 85.57%"', 'UNSUPPORTED',
                  'No BARR per-stratum measurement exists. 53.21% is the Global MedFiLM TINY stratum value. Removed.'],
                 ['"Independent external multi-center datasets"', 'OVERSTATED',
                  'Reclassified as a single-case external pilot; dataset-level independence not established.'],
                 ['BARR KUB Dice 85.57% and IoU 77.85%', 'UNSUPPORTED',
                  'These are the ROUTER_HOLDOUT KUB value and an unrecorded IoU. Removed from the VAL808 table.']],
                body_pt=8)
    caption('Table 8. Retraction register. Full evidence trail in '
            'reports/audits/c1_external_evidence_v1_0/.')

    # ------------------------------------------------ 9. trust boundary
    h1('9. Trust Boundary Status')
    para('The C1 launch release is frozen at RC3 (digest 54d1273a\u20263549f) and is unmodified by this report. '
         'The production trust root was found to contain agent-generated signing material, and the RC3 gate '
         'currently refuses its own release digest because it delegates identity verification to RC2. '
         'Consequently no scientific execution is authorised, no production grant has been minted, and no '
         'dataset has been opened through a production launch. The trust store is excluded from scientific use '
         'pending accountable human review. This report does not create a trust policy, sign any approval, or '
         'constitute an authorisation.')

    # ------------------------------------------------ 10. what holds
    h1('10. What the Evidence Does Support')
    callout('Defensible summary',
            '1. Global MedFiLM reaches 83.51% macro-domain Dice on VAL808 (n = 808) with 3.52M parameters, '
            'ranking first of six under a single shared protocol, and is not statistically distinguishable '
            'from DeepLabV3+.\n'
            '2. Regional BARR preserves macro Dice relative to Global MedFiLM: +0.28 pp on VAL808 (three-seed '
            'mean) and +0.17 pp on the one-shot ROUTER_HOLDOUT, within a \u22120.5 pp non-inferiority margin. '
            'This is a preservation result, not an improvement claim.\n'
            '3. On in-sample development data the router removes most harmful refinements and the post-safety '
            'filter removes a further 22 cases, at 24.3% of the unconditional refiner workload.\n'
            '4. Four single internal and four single external cases reproduce exactly from the stated '
            'checkpoint, with genuine domain-shift failure modes visible at the pixel level.\n'
            '5. No external validation exists. The external material is a four-case pilot and is reported as '
            'such.',
            fill=HEX_HIGHLIGHT, color=COLOR_PRIMARY)

    p = doc.add_paragraph()
    r = p.add_run('Report date: ' + REPORT_DATE + '  |  RA-MedFiLM-BARR Scientific Investigation Team')
    r.font.size = Pt(8.5); r.font.italic = True; r.font.color.rgb = COLOR_SECONDARY

    out_path = Path('paper_doc/RA_MedFiLM_BARR_Scientific_Report.docx')
    doc.save(out_path)
    print(f'Report successfully saved to {out_path.resolve()}')


if __name__ == '__main__':
    create_report()
