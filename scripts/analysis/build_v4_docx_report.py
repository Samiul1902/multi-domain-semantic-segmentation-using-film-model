"""
Build RA-MedFiLM-BARR Complete Scientific Results Master Report V4 in DOCX format.
Follows all Phase A - Phase J requirements:
18-22 pages equivalent, 14 multi-panel figures, 8 standardized tables,
complete internal evaluation, 4 internal domain galleries, external evaluation,
stage progression, 13-arm ablation, 3-seed reproducibility, interpretability,
perturbation robustness, failure taxonomy, historical TEST1683, and supported vs missing evidence.
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def build_docx_report():
    doc = Document()
    
    # Standard A4 / Letter, 0.7 inch margins
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)
        
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(4)
    
    # ---------------------------------------------------------
    # TITLE & HEADER
    # ---------------------------------------------------------
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(0)
    tp.paragraph_format.space_after = Pt(2)
    tr = tp.add_run("RA-MedFiLM-BARR: Complete Scientific Results Master Report (V4)")
    tr.font.size = Pt(20)
    tr.font.bold = True
    tr.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(10)
    sr = sp.add_run("Risk-Averse Medical Feature-wise Linear Modulation with Boundary-Aware Residual Refinement: Comprehensive Scientific Results, Multimodal Segmentation Atlas & Reproducibility Audit")
    sr.font.size = Pt(11)
    sr.font.italic = True
    sr.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)
    
    # Metadata Table
    meta_table = doc.add_table(rows=2, cols=4)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    hdrs = ["Benchmark Partition", "Internal Validation", "Historical External", "Audit Status"]
    vals = ["VAL808 (Quarantined)", "808 Cases (4 Domains)", "EXTERNAL884 (3 Cohorts)", "Strict Provenance Verified"]
    for i in range(4):
        c_h = meta_table.cell(0, i)
        c_h.text = hdrs[i]
        set_cell_background(c_h, "1B365D")
        c_h.paragraphs[0].runs[0].font.bold = True
        c_h.paragraphs[0].runs[0].font.size = Pt(8)
        c_h.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        c_h.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        c_v = meta_table.cell(1, i)
        c_v.text = vals[i]
        set_cell_background(c_v, "F0F4F8")
        c_v.paragraphs[0].runs[0].font.size = Pt(8)
        c_v.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        c_v.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_margins(c_h, 60, 60, 80, 80)
        set_cell_margins(c_v, 60, 60, 80, 80)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    
    # ---------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY
    # ---------------------------------------------------------
    h1 = doc.add_heading("1. Executive Summary & Methodological Contribution", level=1)
    h1.paragraph_format.space_before = Pt(10)
    h1.paragraph_format.space_after = Pt(4)
    h1.runs[0].font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    p = doc.add_paragraph()
    p.add_run("Multi-domain medical image segmentation requires models to generalize across drastically divergent imaging modalities (dermoscopy, ultrasound, endoscopy, radiography) while preserving millimeter-accurate target contours. Standard monolithic architectures trained across heterogeneous tasks suffer from negative cross-task interference, whereas unconstrained two-stage or cascading networks frequently hallucinate spurious lesions under ambiguous acoustic or radiographic contrast. The ")
    p.add_run("RA-MedFiLM-BARR").bold = True
    p.add_run(" framework addresses this challenge through two structurally distinct contributions: (1) a global task-conditioned backbone (")
    p.add_run("GlobalMedFiLM").bold = True
    p.add_run(") that applies Feature-wise Linear Modulation (FiLM) conditioned on task embeddings to align feature distributions across domains; and (2) a Boundary-Aware Residual Refinement (")
    p.add_run("BARR").bold = True
    p.add_run(") module governed by a fail-closed, risk-averse routing mechanism.")
    
    p2 = doc.add_paragraph()
    p2.add_run("Key Empirical Findings & Documented Limitations:").bold = True
    doc.add_paragraph("1. Internal Multi-Domain Superiority: On the canonical VAL808 benchmark (ISIC: 357, BUSI: 84, KVASIR: 87, KUB: 280), GlobalMedFiLM achieves a macro Dice of 0.8351 (+4.30 pp over standard U-Net). The proposed FULL BARR model achieves 0.8379 (+0.28 pp overall gain, +1.46 pp on bladder stones, +1.06 pp on ureteric stones).")
    doc.add_paragraph("2. Risk-Averse Harm Reduction: Component ablation across 4,957 training samples confirms that unrouted refinement (Arm A1) yields a harmful activation rate of 42.7%. The learned benefit router and post-safety gate (Arm A8) restrict refinement to confident candidates, suppressing unnecessary activations and elevating routed delta Dice to +0.75 pp.")
    doc.add_paragraph("3. Negative Results & Material Clinical Failure Patterns: External retrospective stress evaluation (EXTERNAL884) reveals significant domain-shift degradation, notably on the stone-free negative cohort where the model exhibits a 14/14 false-positive detection rate (mean Dice 0.000). Furthermore, under high Gaussian noise on abdominal radiographs, performance degrades substantially (-36.4 pp). These material limitations prove that post-safety gating does not eliminate false positive generation on completely stone-free imagery.")

    # ---------------------------------------------------------
    # SECTION 2: ARCHITECTURE & DATASET ORGANIZATION
    # ---------------------------------------------------------
    doc.add_heading("2. Methodology, Architecture & Dataset Organization", level=1)
    p = doc.add_paragraph("Figure 1 diagrams the complete RA-MedFiLM-BARR execution pipeline. The network executes a binary foreground segmentation per task: cutaneous lesion (ISIC), breast lesion (BUSI), endoscopic polyp (KVASIR), or urinary calculus (KUB). Anatomical categories (e.g. kidney, ureteric, bladder) are clinical subgroups, not separate output channels.")
    
    if os.path.exists('full_doc_report/figures/fig_arch_method.png'):
        doc.add_picture('full_doc_report/figures/fig_arch_method.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run("Figure 1: RA-MedFiLM-BARR Canonical Execution Architecture. Input -> Task conditioning -> GlobalMedFiLM (G) -> Global Probability -> ROI Proposal -> Benefit Router (B_phi) -> Selective Refiner (R_psi) -> Safety Gate (S_omega) -> Final Mask.")
        r.font.size = Pt(8)
        r.font.italic = True

    # Dataset Summary Table
    doc.add_paragraph("Table 1: Cohort Partitioning and Anatomical Grouping Summary").bold = True
    t1 = doc.add_table(rows=6, cols=6)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1.autofit = False
    t1_data = [
        ["Domain / Dataset", "Modality", "Foreground Target", "TRAIN5832", "VAL808", "Historical TEST1683"],
        ["ISIC 2018", "Dermoscopy", "Cutaneous Pigmented Lesion", "2,594", "357", "735"],
        ["BUSI-WHU", "Breast Ultrasound", "Benign & Malignant Masses", "610", "84", "174"],
        ["Kvasir-SEG", "Colonoscopy", "Gastrointestinal Mucosal Polyp", "632", "87", "216"],
        ["KUB-StoneX", "Abdominal Radiography", "Kidney, Ureteric & Bladder Stones", "1,996", "280", "558"],
        ["Total Pooled", "4 Heterogeneous Modalities", "Binary Target per Task", "5,832", "808", "1,683"]
    ]
    for r_i, row in enumerate(t1_data):
        for c_i, val in enumerate(row):
            cell = t1.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 3 else WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(8)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 5:
                set_cell_background(cell, "D9E2EC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(8)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(8)
            set_cell_margins(cell, 60, 60, 80, 80)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ---------------------------------------------------------
    # SECTION 3: COMPLETE INTERNAL MODEL EVALUATION
    # ---------------------------------------------------------
    doc.add_heading("3. Complete Internal Model Evaluation (Six Architectures)", level=1)
    p = doc.add_paragraph("Table 2 and Figure 2 benchmark the primary proposed model against five external baselines evaluated on identical VAL808 splits. GlobalMedFiLM establishes clear macro superiority (0.8351 vs 0.7878–0.8277), while BARR provides targeted residual improvements.")
    
    if os.path.exists('full_doc_report/figures/fig_internal_performance_summary.png'):
        doc.add_picture('full_doc_report/figures/fig_internal_performance_summary.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run("Figure 2: Internal Model Evaluation Summary across Six Competing Architectures (Heatmap, Paired Baseline Differences, and Domain Metric Boxplots).")
        r.font.size = Pt(8)
        r.font.italic = True

    # Insert Table 2: Six Models
    doc.add_paragraph("Table 2: Six-Model Comparative Performance Matrix on VAL808").bold = True
    t2 = doc.add_table(rows=8, cols=8)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2.autofit = False
    t2_data = [
        ["Model Architecture", "Parameters", "Analytical GMACs", "Macro Dice", "ISIC Dice", "BUSI Dice", "KVASIR Dice", "KUB Dice"],
        ["U-Net (Standard)", "7.76M", "46.14", "0.7878", "0.8553", "0.8198", "0.7552", "0.7211"],
        ["Attention U-Net", "7.85M", "47.22", "0.7890", "0.8617", "0.8277", "0.7710", "0.6958"],
        ["U-Net++", "9.16M", "137.94", "0.7920", "0.8601", "0.8163", "0.7710", "0.7207"],
        ["DeepLabV3+", "40.35M", "69.14", "0.8277", "0.8853", "0.8669", "0.8197", "0.7387"],
        ["Transformer / MiT U-Net", "16.35M", "99.10", "0.8224", "0.8871", "0.8640", "0.8133", "0.7252"],
        ["GlobalMedFiLM (Baseline)", "3.52M", "31.55", "0.8351", "0.8972", "0.8588", "0.8202", "0.7641"],
        ["RA-MedFiLM-BARR (Proposed)", "4.84M", "32.44*", "0.8379", "0.8982", "0.8589", "0.8210", "0.7734"]
    ]
    for r_i, row in enumerate(t2_data):
        for c_i, val in enumerate(row):
            cell = t2.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 1 else WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 7:
                set_cell_background(cell, "D9E2EC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 50, 50, 60, 60)
            
    doc.add_paragraph("*Note: RA-MedFiLM-BARR GMACs reflect expected conditional execution under Arm A8 budget.").paragraph_format.space_after = Pt(6)

    # ---------------------------------------------------------
    # SECTION 4: DOMAIN, CLASS & SUBCLASS EVALUATION
    # ---------------------------------------------------------
    doc.add_heading("4. Domain, Class and Subclass Performance Analysis", level=1)
    p = doc.add_paragraph("Figure 3 and Table 3 detail clinical subgroup performance. Note: Histological pathology is validated for BUSI (Benign: 60, Malignant: 24); KUB categories reflect verified radiological stone sites (Bladder, Kidney, Ureteric); Kvasir polyps are stratified by median ground truth area; ISIC cases represent task-level lesion segmentation.")
    
    if os.path.exists('full_doc_report/figures/fig5_domain_subgroup_matrix.png'):
        doc.add_picture('full_doc_report/figures/fig5_domain_subgroup_matrix.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run("Figure 3: Multi-Domain (A) and Verified Subgroup (B) Quantitative Profile comparing GlobalMedFiLM and FULL BARR.")
        r.font.size = Pt(8)
        r.font.italic = True

    # ---------------------------------------------------------
    # SECTION 5: INTERNAL QUALITATIVE GALLERIES (FIGS 4-7)
    # ---------------------------------------------------------
    doc.add_heading("5. Internal Four-Domain Qualitative Semantic Segmentation", level=1)
    p = doc.add_paragraph("Figures 4–7 display genuine semantic segmentation visualizations from the frozen validation cohort. Columns show: Native Medical Image, Expert Ground Truth Mask, GlobalMedFiLM Baseline, FULL BARR Refinement, and Triple-Color Overlay (TP: Green, FP: Red, FN: Blue).")
    
    # Fig 4: ISIC
    if os.path.exists('full_doc_report/figures/fig1_isic_cases.png'):
        doc.add_picture('full_doc_report/figures/fig1_isic_cases.png', width=Inches(6.6))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 4: ISIC 2018 Dermoscopy Qualitative Segmentation Grid (Typical, High-Performing, Boundary-Challenging, and Follicular Occlusion Failure).").font.size = Pt(8)
        
    # Fig 5: BUSI
    if os.path.exists('full_doc_report/figures/fig2_busi_subclasses.png'):
        doc.add_picture('full_doc_report/figures/fig2_busi_subclasses.png', width=Inches(6.6))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 5: BUSI-WHU Breast Ultrasound Segmentation across Verified Subclasses (Benign Masses vs Malignant Carcinomas).").font.size = Pt(8)

    # Fig 6: KVASIR
    if os.path.exists('full_doc_report/figures/fig3_kvasir_cases.png'):
        doc.add_picture('full_doc_report/figures/fig3_kvasir_cases.png', width=Inches(6.6))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 6: Kvasir-SEG Colonoscopy Segmentation across Morphological Scales (Large, Typical, Small/Sessile, and Glare Failure).").font.size = Pt(8)

    # Fig 7: KUB
    if os.path.exists('full_doc_report/figures/fig4_kub_subclasses.png'):
        doc.add_picture('full_doc_report/figures/fig4_kub_subclasses.png', width=Inches(6.6))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 7: KUB-StoneX Plain Abdominal Radiographs across Verified Stone Sites (Bladder, Kidney, Ureteric, and Punctate Failure). Note: Full-field radiographs shown.").font.size = Pt(8)

    # ---------------------------------------------------------
    # SECTION 6: EXTERNAL RETROSPECTIVE EVALUATION
    # ---------------------------------------------------------
    doc.add_heading("6. External Retrospective Evaluation & Stress Testing", level=1)
    p = doc.add_paragraph("Table 4 and Figures 8–9 evaluate models under retrospective domain shift across 884 external cases: CVC-ClinicDB (colonoscopy, n=612), BrEaST-Lesions-USG (ultrasound, n=252), and Stones_where_are_you (radiography, n=20).")
    
    if os.path.exists('full_doc_report/figures/fig_external_stress_test.png'):
        doc.add_picture('full_doc_report/figures/fig_external_stress_test.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 8: External Retrospective Stress Testing (Domain Shift Degradation vs Internal Benchmark).").font.size = Pt(8)

    if os.path.exists('full_doc_report/figures/fig_external_qualitative_gallery.png'):
        doc.add_picture('full_doc_report/figures/fig_external_qualitative_gallery.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 9: External Qualitative Case Gallery (Accepted Beneficial, Accepted Harmful, Safety Rejected, Non-Selected, and Stone-Free False-Positive Failure).").font.size = Pt(8)

    # Table 4: External Evidence
    doc.add_paragraph("Table 4: Retrospective External Cohort Stress Performance Summary (EXTERNAL884)").bold = True
    t4 = doc.add_table(rows=5, cols=8)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4.autofit = False
    t4_data = [
        ["External Cohort", "Analogue", "N", "Global Dice", "FULL Dice", "Paired Δ (pp)", "Harm Rate", "Material Failure Status"],
        ["CVC-ClinicDB", "KVASIR", "612", "0.6866", "0.6897", "+0.318", "27.7%", "Moderate domain shift (-13.4 pp vs VAL)"],
        ["BrEaST-Lesions-USG", "BUSI", "252", "0.7078", "0.7081", "+0.028", "12.5%", "Acoustic shift (-15.1 pp vs VAL)"],
        ["Stones (Stone-Positive)", "KUB", "6", "0.2695", "0.2738", "+0.429", "0.0%", "Severe transfer degradation"],
        ["Stones (Stone-Free Neg.)", "KUB", "14", "0.0000", "0.0000", "0.000", "N/A", "14 / 14 FALSE POSITIVE DETECTIONS"]
    ]
    for r_i, row in enumerate(t4_data):
        for c_i, val in enumerate(row):
            cell = t4.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 4:
                set_cell_background(cell, "FFECEC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0x99, 0x00, 0x00)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 50, 50, 60, 60)

    # ---------------------------------------------------------
    # SECTION 7: STAGE-WISE PROGRESSION & PROPAGATION
    # ---------------------------------------------------------
    doc.add_heading("7. Model Progression & Stage-Wise Error Propagation", level=1)
    p = doc.add_paragraph("Figure 10 illustrates how candidate proposals flow through the benefit router and safety gate. In ROUTER_DEVELOPMENT (n=4,957), 1,239 proposals are routed, 1,205 adopted, and 34 unsafe refinements rejected, yielding 815 improved cases and 390 worsened cases. Note on dataset progression: A thorough audit confirms that an incremental multi-seed domain addition experiment was not executed in the repository (INCREMENTAL_DATASET_PROGRESSION_NOT_EXECUTED).")
    
    if os.path.exists('full_doc_report/figures/fig_sankey_routing_safety.png'):
        doc.add_picture('full_doc_report/figures/fig_sankey_routing_safety.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 10: Stage-Wise Proposal Routing & Safety Acceptance Sankey Flow (ROUTER_DEVELOPMENT vs External Retrospective).").font.size = Pt(8)

    # ---------------------------------------------------------
    # SECTION 8: 13-ARM ABLATION STUDY
    # ---------------------------------------------------------
    doc.add_heading("8. Complete 13-Arm Component Ablation Study", level=1)
    p = doc.add_paragraph("Figure 11 and Table 5 detail the Phase 28 13-arm ablation matrix (A0–A8, R1–R3, F1). Always-refine (A1) causes 42.7% harmful activations. Learned routing (A7) lifts delta Dice to +0.72 pp. Post-safety (A8) eliminates 34 negative outliers, elevating delta to +0.75 pp. However, the contrast A8 vs A7 95% CI spans zero, indicating that the incremental mean Dice effect is descriptive rather than statistically proven.")
    
    if os.path.exists('full_doc_report/figures/fig9_ablation_13arm_routed.png'):
        doc.add_picture('full_doc_report/figures/fig9_ablation_13arm_routed.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 11: 13-Arm Ablation Study: Routed Delta Dice and Harmful Activation Share across Architectural Variants.").font.size = Pt(8)

    # Table 5: 13 Arms
    doc.add_paragraph("Table 5: 13-Arm Ablation Primary Metrics (ROUTER_DEVELOPMENT, n=4,957)").bold = True
    t5 = doc.add_table(rows=14, cols=7)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    t5.autofit = False
    t5_data = [
        ["Arm", "Component Configuration Description", "Routed N", "Budget", "Mean Routed Δ", "Improved", "Harmful Share"],
        ["A0", "Global-only baseline (no refinement)", "0", "0.00", "0.0000", "0", "0.0%"],
        ["A1", "Unconditional always-refine endpoint", "4,957", "1.00", "+0.0017", "2,775", "42.7%"],
        ["A2", "Random proposal routing (budget 0.25)", "1,239", "0.25", "+0.0014", "669", "44.4%"],
        ["A3", "Entropy-based proposal routing", "1,239", "0.25", "+0.0072", "844", "31.9%"],
        ["A4", "Margin-based uncertainty routing", "1,239", "0.25", "+0.0071", "843", "32.0%"],
        ["A5", "ROI-size heuristic proposal routing", "1,239", "0.25", "-0.0004", "597", "46.4%"],
        ["A6", "Learned benefit router (without cost loss)", "1,239", "0.25", "+0.0072", "827", "33.3%"],
        ["A7", "Learned benefit router + resource cost loss", "1,239", "0.25", "+0.0072", "827", "33.3%"],
        ["A8", "Canonical FULL BARR (+ post-safety gate)", "1,205", "0.24", "+0.0075", "815", "32.4%"],
        ["R1", "Router without deep feature backbone input", "1,239", "0.25", "+0.0033", "723", "37.4%"],
        ["R2", "Router without task identity conditioning", "1,239", "0.25", "+0.0012", "678", "43.5%"],
        ["R3", "Scalar-only metadata router", "1,239", "0.25", "+0.0013", "702", "42.3%"],
        ["F1", "Refiner without p_global input probability", "1,239", "0.25", "-0.0326", "256", "68.8%"]
    ]
    for r_i, row in enumerate(t5_data):
        for c_i, val in enumerate(row):
            cell = t5.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 9:
                set_cell_background(cell, "D9E2EC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(7)
            set_cell_margins(cell, 40, 40, 50, 50)

    # ---------------------------------------------------------
    # SECTION 9: STATISTICAL REPRODUCIBILITY (3 SEEDS)
    # ---------------------------------------------------------
    doc.add_heading("9. Statistical Reproducibility across Random Seeds", level=1)
    p = doc.add_paragraph("Table 6 and Figure 12 report three-seed evaluation across Seeds 42, 123, and 3407 on VAL808. Crucial methodological disclosure: All three runs share an identical frozen GlobalMedFiLM backbone. Variance reflects refiner and router weight initialization, not end-to-end model retrainings.")
    
    if os.path.exists('full_doc_report/figures/figE_seedwise_reproducibility_shared_backbone.png'):
        doc.add_picture('full_doc_report/figures/figE_seedwise_reproducibility_shared_backbone.png', width=Inches(6.6))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 12: Seed-Wise Reproducibility Distribution across Shared Backbone Initialization Seeds.").font.size = Pt(8)

    # Table 6: Seeds
    doc.add_paragraph("Table 6: Three-Seed Refinement Reproducibility Summary on VAL808").bold = True
    t6 = doc.add_table(rows=5, cols=7)
    t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    t6.autofit = False
    t6_data = [
        ["Seed", "Global Baseline Dice", "Final BARR Dice", "Net Shift (Δ pp)", "Routed Count", "Adopted Count", "Harmful Count"],
        ["Seed 42", "0.835079", "0.837862", "+0.2783", "183", "165", "31"],
        ["Seed 123", "0.835079", "0.837910", "+0.2831", "185", "168", "29"],
        ["Seed 3407", "0.835079", "0.837815", "+0.2736", "181", "163", "33"],
        ["Mean ± SD", "0.835079 ± 0.000", "0.837862 ± 0.00004", "+0.2783 ± 0.004", "183 ± 2", "165 ± 2", "31 ± 2"]
    ]
    for r_i, row in enumerate(t6_data):
        for c_i, val in enumerate(row):
            cell = t6.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 1 else WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 4:
                set_cell_background(cell, "D9E2EC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 50, 50, 60, 60)

    # ---------------------------------------------------------
    # SECTION 10: PERTURBATION ROBUSTNESS & FAILURE TAXONOMY
    # ---------------------------------------------------------
    doc.add_heading("10. Perturbation Robustness & Comprehensive Failure Taxonomy", level=1)
    p = doc.add_paragraph("Table 7 and Figure 13 document model sensitivity under systematic image perturbations (Gaussian noise, Gaussian blur, contrast, brightness, gamma, resolution) and categorize principal failure mechanisms.")
    
    if os.path.exists('full_doc_report/figures/fig_failure_taxonomy_distribution.png'):
        doc.add_picture('full_doc_report/figures/fig_failure_taxonomy_distribution.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 13: Failure Taxonomy & Robustness Perturbation Degradation Profiles.").font.size = Pt(8)

    # Table 7: Perturbation & Failures
    doc.add_paragraph("Table 7: Domain Perturbation Sensitivity (Mean Paired Δ Dice pp)").bold = True
    t7 = doc.add_table(rows=7, cols=5)
    t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    t7.autofit = False
    t7_data = [
        ["Perturbation Condition", "BUSI Ultrasound", "ISIC Dermoscopy", "KVASIR Endoscopy", "KUB Radiography"],
        ["Gaussian Noise (High)", "-8.99 pp", "-3.15 pp", "-6.04 pp", "-36.36 pp (Catastrophic)"],
        ["Gaussian Blur (High)", "-0.31 pp", "-0.50 pp", "-1.44 pp", "-5.63 pp"],
        ["Resolution (0.50x)", "-0.37 pp", "-0.46 pp", "-1.66 pp", "-5.44 pp"],
        ["Low Gamma", "-1.27 pp", "-0.25 pp", "-0.94 pp", "-0.43 pp"],
        ["Low Contrast", "-0.24 pp", "-0.53 pp", "-0.05 pp", "-0.48 pp"],
        ["Negative Brightness", "-0.60 pp", "-0.09 pp", "-0.79 pp", "-1.67 pp"]
    ]
    for r_i, row in enumerate(t7_data):
        for c_i, val in enumerate(row):
            cell = t7.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 1 else WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 1:
                set_cell_background(cell, "FFECEC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 50, 50, 60, 60)

    # ---------------------------------------------------------
    # SECTION 11: COMPUTATIONAL EFFICIENCY & PARETO FRONTIER
    # ---------------------------------------------------------
    doc.add_heading("11. Computational Complexity & Latency Measurements", level=1)
    p = doc.add_paragraph("Figure 14 plots the Accuracy vs. GMACs Pareto frontier. RA-MedFiLM-BARR delivers superior macro Dice (0.8379) at an analytical complexity of 32.44 GMACs, outperforming DeepLabV3+ (69.14 GMACs, 40.35M params) and Transformer MiT U-Net (99.10 GMACs, 16.35M params) while maintaining a mean single-image forward latency of 15.72 ms (skip path) to 18.89 ms (executed path) on an NVIDIA RTX 3060 Ti.")
    
    if os.path.exists('full_doc_report/figures/fig_accuracy_vs_cost_detail.png'):
        doc.add_picture('full_doc_report/figures/fig_accuracy_vs_cost_detail.png', width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 14: Computational Complexity vs Accuracy Pareto Trade-off Frontier.").font.size = Pt(8)

    # ---------------------------------------------------------
    # SECTION 12: HISTORICAL TEST1683 EVALUATION
    # ---------------------------------------------------------
    doc.add_heading("12. Historical TEST1683 Benchmark Disclosure", level=1)
    p = doc.add_paragraph("Disclosure of Prior Exposure: In Phase 39 (revision v1.2), the prospective TEST partition (n=1,683) was evaluated following two earlier disclosed process exits. The historical one-shot macro Dice achieved was 0.8314 across 1,683 test cases (ISIC n=735: 0.8869, BUSI n=174: 0.8504, KVASIR n=216: 0.8507, KUB n=558: 0.7377). In strict compliance with research governance, the present V4 report does not open, re-read, or evaluate TEST1683 images, preserving historical integrity.")

    # ---------------------------------------------------------
    # SECTION 13: SUPPORTED FINDINGS VS MISSING EVIDENCE
    # ---------------------------------------------------------
    doc.add_heading("13. Scientific Claims, Novelty & Critical Evidence Gaps", level=1)
    
    doc.add_paragraph("Table 8: Matrix of Experimentally Supported Findings vs Unresolved Research Questions").bold = True
    t8 = doc.add_table(rows=9, cols=3)
    t8.alignment = WD_TABLE_ALIGNMENT.CENTER
    t8.autofit = False
    t8_data = [
        ["Evidence Category", "Status", "Scientific Finding / Documented Evidence Gap"],
        ["Internal Multi-Domain Gain", "SUPPORTED", "GlobalMedFiLM achieves 0.8351 macro Dice; FULL BARR achieves 0.8379 (+0.28 pp overall gain on VAL808)."],
        ["Risk-Averse Routing Dynamics", "SUPPORTED", "Learned routing cuts harmful activations from 42.7% (A1) to 32.4% (A8), raising routed delta to +0.75 pp."],
        ["Anatomical Subgroup Refinements", "SUPPORTED", "Verified gains on Bladder Stones (+1.46 pp) and Ureteric Stones (+1.06 pp) in plain radiography."],
        ["External Domain Shift Fragility", "MATERIAL FAILURE", "Material failure on stone-free radiographs (14/14 false positive detections; Dice 0.000)."],
        ["C1 Causal FiLM Attribution Study", "MISSING EVIDENCE", "0 of 6 planned genuine paired C1 training runs executed; causal FiLM attribution remains unproven."],
        ["C2 Causal Component Attribution", "MISSING EVIDENCE", "Component ablations conducted in-sample on ROUTER_DEVELOPMENT; causal held-out validation pending."],
        ["C3 24-Cell Baseline Comparison", "MISSING EVIDENCE", "0 of 24 genuine matched multi-seed baseline cells completed; comparative claims limited to Phase 21."],
        ["Incremental Domain Progression", "MISSING EVIDENCE", "Incremental dataset training was not executed in repository (INCREMENTAL_DATASET_PROGRESSION_NOT_EXECUTED)."]
    ]
    for r_i, row in enumerate(t8_data):
        for c_i, val in enumerate(row):
            cell = t8.cell(r_i, c_i)
            cell.text = val
            p = cell.paragraphs[0]
            if c_i == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if r_i == 0:
                set_cell_background(cell, "1B365D")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif "FAILURE" in val or "MISSING" in val:
                set_cell_background(cell, "FFF5F5" if "FAILURE" in val else "F7FAFC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xC5, 0x30, 0x30) if "FAILURE" in val else RGBColor(0x71, 0x80, 0x96)
            else:
                set_cell_background(cell, "F0FFF4" if "SUPPORTED" in val else "FFFFFF")
                p.runs[0].font.size = Pt(7.5)
                if "SUPPORTED" in val:
                    p.runs[0].font.color.rgb = RGBColor(0x27, 0x67, 0x49)
            set_cell_margins(cell, 50, 50, 60, 60)

    # ---------------------------------------------------------
    # SECTION 14: CONCLUSION & PUBLICATION READINESS
    # ---------------------------------------------------------
    doc.add_heading("14. Conclusion & Scientific Submission Guidance", level=1)
    p_end = doc.add_paragraph()
    p_end.add_run("The RA-MedFiLM-BARR research lifecycle establishes that task-conditioned FiLM representations paired with selective, risk-averse residual refinement achieve robust multi-domain segmentation performance without the excessive computational overhead of large vision transformers. However, submission to premier journals (IEEE TMI / Medical Image Analysis) requires transparent disclosure of external transfer vulnerabilities, specifically the stone-free false positive detection rate, and explicit acknowledgment that causal FiLM attribution (C1) and 24-cell matched baseline comparisons (C3) remain future experimental milestones. The complete code, checkpoints, prediction masks, and numerical evidence are archived for independent scientific verification.")
    
    out_path = 'full_doc_report/RA_MedFiLM_BARR_Complete_Scientific_Results_V4.docx'
    doc.save(out_path)
    print(f'Saved DOCX: {out_path}')

build_docx_report()
