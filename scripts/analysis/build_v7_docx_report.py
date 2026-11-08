"""
Build ReMedFiLM Complete Scientific Methodology, Experimental Evaluation and Results V7 in DOCX format:
ReMedFiLM_Complete_Scientific_Report_V7.docx

Full reconstruction around:
- Proposed model: ReMedFiLM (FULL RA-MedFiLM-BARR, 4.84M parameters: G + B_phi + R_psi + S_omega)
- Internal global backbone: GlobalMedFiLM (3.52M params, Arm A0 comparator)
- Complete external evaluation matrices: CVC-ClinicDB (612), BrEaST-USG (252), Stones (20: 6 positive, 14 negative controls)
- Complete visual figures: FIG01, F03, F04, F05, F06-F09, F10, F11, F12, F15, F17, F18, F19
- Rigorous statistical claims (purged p<10^-4, accurate percentile bootstrap non-inferiority preservation)
- Transparent negative disclosures (14/14 stone-free false positives, -36.36 pp noise collapse on KUB)
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

def set_cell_margins(cell, top=70, bottom=70, left=90, right=90):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def build_v7_docx():
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)
        
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(9.5)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # Document Header
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("ReMedFiLM: Complete Scientific Methodology, Experimental Evaluation and Results")
    r_title.bold = True
    r_title.font.size = Pt(20)
    r_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Task-Conditioned Global-to-Regional Medical Image Segmentation with Risk-Averse Refinement | Canonical V7.0 Report")
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    # Callout Banner
    tbl_meta = doc.add_table(rows=1, cols=1)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = tbl_meta.cell(0, 0)
    set_cell_background(c, "EBF8FF")
    set_cell_margins(c, 100, 100, 140, 140)
    p_box = c.paragraphs[0]
    p_box.paragraph_format.space_after = Pt(2)
    r_b = p_box.add_run("OFFICIAL CANONICAL ARCHITECTURE & REPRODUCIBILITY AUDIT:\n")
    r_b.bold = True
    r_b.font.size = Pt(9)
    r_b.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)
    r_txt = p_box.add_run(
        "• Central Proposed Method: ReMedFiLM (composed 4.84M architecture: G + B_phi + R_psi + S_omega, historically designated FULL RA-MedFiLM-BARR).\n"
        "• Internal Backbone & Baseline Comparator: GlobalMedFiLM (G, 3.52M params, Arm A0 baseline).\n"
        "• Modular Training: 4-stage freeze composition with zero trainable parameters in the assembly harness (no joint backprop).\n"
        "• Core Scientific Finding: Naive secondary refinement is unsafe (42.7% harm rate); ReMedFiLM risk-averse routing cuts all-population harm to 7.87% while preserving/improving paired Dice (+0.28 pp dev mean).\n"
        "• Transparent Negative Disclosures: 14/14 false positive detections on stone-free radiographs (Dice 0.000); -36.36 pp noise sensitivity on KUB."
    )
    r_txt.font.size = Pt(8.5)
    r_txt.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 1: Executive Summary
    doc.add_heading("1. Executive Summary & Problem Formulation", level=1)
    doc.add_paragraph(
        "Medical image segmentation across diverse clinical modalities poses severe scale and contrast dilemmas. Macroscopic lesions (cutaneous melanoma, large breast tumors) demand broad contextual abstraction, whereas microscopic and subtle targets (sub-centimeter renal calculi, sessile polyps) require high-resolution boundary analysis. Traditional monolithic architectures either over-parameterize global features or introduce negative task interference across modalities."
    )
    doc.add_paragraph(
        "ReMedFiLM resolves this through a staged, risk-averse hierarchical pipeline. A task-conditioned global encoder–decoder (GlobalMedFiLM, 3.52M parameters) produces full-canvas context. When ambiguous targets are localized, a learned Benefit Router (B_phi, 36.8K parameters) evaluates whether secondary refinement provides expected utility exceeding computational cost. If approved, a dedicated Regional Residual Refiner (R_psi, 1.28M parameters) generates localized boundary corrections, followed by a Post-Safety Filter (S_omega, 1.22K parameters) providing fail-closed rollback against hallucination."
    )

    # Section 2: Canonical Methodology & Figure 1
    doc.add_heading("2. Canonical ReMedFiLM Architecture & Mathematical Formulation", level=1)
    
    img_f01 = 'full_doc_report/figures/FIG01_ReMedFiLM_Methodology_V7.png'
    if os.path.exists(img_f01):
        doc.add_picture(img_f01, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 1: Complete Canonical Architecture of ReMedFiLM (FULL Proposed 4.84M Modular Assembly).").font.size = Pt(8)

    doc.add_paragraph(
        "Mathematical Formulations:\n"
        "1. FiLM Modulation in GlobalMedFiLM: F_hat = (1 + tanh(gamma(e_t))) * F + tanh(beta(e_t)), with e_t = E(t) in R^32. Zero-initialization ensures pure identity mapping at initialization.\n"
        "2. Benefit Router Utility: U = Delta_hat - lambda * CostRatio, where lambda = 0.25 and CostRatio = 1,051,648 / 10,270,749. Execution threshold tau_C8 = -0.024358.\n"
        "3. Three Execution Outcomes: (1) SKIP -> p_global (31.55 GMACs); (2) REFINE + ACCEPT -> p_cand spatial insertion crop (34.72 GMACs amortized); (3) REFINE + REJECT -> fail-closed fallback to p_global (44.61 GMACs)."
    )

    # Section 3: Internal Model Comparison
    doc.add_heading("3. Internal Benchmark Evaluation (VAL808)", level=1)
    doc.add_paragraph(
        "Table 1 and Figure 3 present the seven-model comparison across 808 validation images spanning ISIC 2018, BUSI-WHU, Kvasir-SEG, and KUB-StoneX. ReMedFiLM achieves 83.79% macro domain mean Dice, providing non-inferior preservation (+0.28 pp dev mean over GlobalMedFiLM backbone)."
    )

    img_f03 = 'full_doc_report/figures/F03_Internal_Model_Comparison_ReMedFiLM.png'
    if os.path.exists(img_f03):
        doc.add_picture(img_f03, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 3: Internal 7-Model VAL808 Benchmark & Efficiency-Accuracy Pareto Frontier.").font.size = Pt(8)

    # Table 1: Internal Model Comparison
    t1 = doc.add_table(rows=8, cols=7)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1_data = [
        ["Model Architecture", "Role / Protocol", "Params", "GMACs", "Macro Dice (%)", "95% CI", "Statistical Status vs Backbone"],
        ["Standard U-Net", "External Baseline", "7.76M", "30.50", "78.78%", "[73.81, 83.75]", "Significantly Inferior (p < 0.05)"],
        ["Attention U-Net", "External Baseline", "7.85M", "32.10", "78.90%", "[72.88, 84.47]", "Significantly Inferior (p < 0.05)"],
        ["U-Net++", "External Baseline", "9.16M", "34.20", "79.20%", "[74.46, 83.82]", "Significantly Inferior (p < 0.05)"],
        ["MiT-Transformer", "External Baseline", "16.35M", "28.45", "82.24%", "[75.99, 87.55]", "Significantly Inferior (p < 0.05)"],
        ["DeepLabV3+", "External Baseline", "40.35M", "41.19", "82.77%", "[77.07, 87.61]", "Non-Significant (CI Overlaps 0)"],
        ["GlobalMedFiLM (G)", "Internal Backbone", "3.52M", "31.55", "83.51%", "[78.77, 87.80]", "Reference Comparator (Arm A0)"],
        ["ReMedFiLM (Proposed)", "FULL Modular Assembly", "4.84M", "34.72", "83.79%", "[83.73, 83.85]*", "Paired Preservation (+0.28 pp mean)"]
    ]
    for r_i, r_data in enumerate(t1_data):
        bg = "D9E2EC" if r_i == 7 else ("1B365D" if r_i == 0 else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF"))
        for c_i, v in enumerate(r_data):
            cell = t1.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_background(cell, bg)
            p.runs[0].font.size = Pt(7.5)
            if r_i == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 7:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
            set_cell_margins(cell, 40, 40, 50, 50)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 4: Domain & Subclass Performance
    doc.add_heading("4. Four-Domain Breakdown & Anatomical Subclasses", level=1)
    
    img_f04 = 'full_doc_report/figures/F04_Domain_Wise_Performance_ReMedFiLM.png'
    if os.path.exists(img_f04):
        doc.add_picture(img_f04, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 4: Domain-Wise Performance Profile and Paired Forest Plot across ISIC, BUSI, KVASIR, and KUB.").font.size = Pt(8)

    doc.add_paragraph(
        "Subgroup analysis demonstrates that ReMedFiLM provides targeted improvements on high-ambiguity targets. In KUB plain radiography, where stone boundaries blend into pelvic bone trabeculae, ReMedFiLM improves Bladder Stone Dice by +1.46 pp (73.39% -> 74.86%) and Ureteric Stones by +1.06 pp (79.39% -> 80.45%). On macroscopic breast tumors where GlobalMedFiLM is already optimal, the router safely executes pass-through (100% harm-filtered on benign lesions)."
    )

    # Section 5: Semantic Segmentation Galleries
    doc.add_heading("5. Semantic Segmentation Qualitative Galleries", level=1)
    doc.add_paragraph(
        "Figures 6–9 display matched qualitative segmentation results comparing Original Images, Ground Truth, GlobalMedFiLM predictions, ReMedFiLM final segmentations, and color-coded error maps (TP: Green, FP: Red, FN: Blue)."
    )

    for fig_file, cap_text in [
        ('full_doc_report/figures/fig1_isic_cases.png', 'Figure 6: ISIC 2018 Dermoscopy Qualitative Cases across Typical, High, Challenging, and Failure Regimes.'),
        ('full_doc_report/figures/fig2_busi_subclasses.png', 'Figure 7: BUSI-WHU Breast Ultrasound Qualitative Cases Stratified by Benign vs Malignant Pathology.'),
        ('full_doc_report/figures/fig3_kvasir_cases.png', 'Figure 8: Kvasir-SEG Endoscopic Polyp Qualitative Cases across Scale and Specular Challenges.'),
        ('full_doc_report/figures/fig4_kub_subclasses.png', 'Figure 9: KUB-StoneX Plain Radiography Qualitative Cases across Bladder, Kidney, and Ureteric Stones.')
    ]:
        if os.path.exists(fig_file):
            doc.add_picture(fig_file, width=Inches(6.6))
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.add_run(cap_text).font.size = Pt(8)

    # Section 6: Complete External Evaluation Matrix
    doc.add_heading("6. Retrospective External Cohort Evaluation (N=884)", level=1)
    doc.add_paragraph(
        "To evaluate real-world generalizability, ReMedFiLM was audited against 884 retrospective external images: CVC-ClinicDB (612 colonoscopy polyps), BrEaST-Lesions-USG (252 breast ultrasound lesions), and Stones_where_are_you (20 abdominal plain radiographs, comprising 6 stone-positive and 14 stone-free normal controls)."
    )

    img_f11 = 'full_doc_report/figures/F11_External_Quantitative_Evaluation_ReMedFiLM.png'
    if os.path.exists(img_f11):
        doc.add_picture(img_f11, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 11: Retrospective External Quantitative Evaluation Profile across 884 Cases.").font.size = Pt(8)

    # Table 4: External Evaluation Performance Matrix
    doc.add_paragraph("Table 4: External Performance Matrix (ReMedFiLM vs GlobalMedFiLM Backbone)")
    t4 = doc.add_table(rows=6, cols=7)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4_data = [
        ["External Cohort", "Modality Analogue", "N", "Global Dice", "ReMedFiLM Dice", "Delta (pp)", "Evidence Classification"],
        ["CVC-ClinicDB", "Colonoscopy Polyp", "612", "0.6866", "0.6897", "+0.31 pp", "Retrospective Exploratory"],
        ["BrEaST-Lesions-USG", "Breast Ultrasound", "252", "0.7078", "0.7081", "+0.03 pp", "Retrospective Exploratory"],
        ["Stones_where_are_you (All)", "Abdominal Radiograph", "20", "0.0808", "0.0821", "+0.13 pp", "Retrospective Exploratory"],
        ["Stones (Stone-Positive)", "Radiograph (Positive)", "6", "0.2695", "0.2738", "+0.43 pp", "Target Present"],
        ["Stones (Stone-Free)", "Radiograph (Negative)", "14", "0.0000", "0.0000", "+0.00 pp", "14/14 False Positive (Material Failure)"]
    ]
    for r_i, r_data in enumerate(t4_data):
        bg = "FFF5F5" if r_i == 5 else ("1B365D" if r_i == 0 else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF"))
        for c_i, v in enumerate(r_data):
            cell = t4.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_background(cell, bg)
            p.runs[0].font.size = Pt(7.5)
            if r_i == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 5:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xC5, 0x30, 0x30)
            set_cell_margins(cell, 35, 35, 45, 45)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Table 4B: External Routing and Safety Matrix
    doc.add_paragraph("Table 4B: External Routing & Safety Gating Breakdown")
    t4b = doc.add_table(rows=4, cols=7)
    t4b.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4b_data = [
        ["External Cohort", "Total N", "Routed Count", "Refined Count", "Safety Rejected", "Safety Accepted", "Harm Rate of Adopted"],
        ["CVC-ClinicDB", "612", "118", "118", "35", "83", "16.87% (14 worsened)"],
        ["BrEaST-Lesions-USG", "252", "56", "56", "9", "47", "42.55% (20 worsened)"],
        ["Stones_where_are_you", "20", "10", "10", "1", "9", "0.00% (0 worsened, 7 unchanged)"]
    ]
    for r_i, r_data in enumerate(t4b_data):
        bg = "1B365D" if r_i == 0 else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF")
        for c_i, v in enumerate(r_data):
            cell = t4b.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 1 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_background(cell, bg)
            p.runs[0].font.size = Pt(7.5)
            if r_i == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            set_cell_margins(cell, 35, 35, 45, 45)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    img_f12 = 'full_doc_report/figures/F12_External_Qualitative_Composite_ReMedFiLM.png'
    if os.path.exists(img_f12):
        doc.add_picture(img_f12, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 12: External Qualitative Segmentation Composite (CVC-ClinicDB, BrEaST-USG, Stones).").font.size = Pt(8)

    # Section 7: 13-Arm Component Ablation
    doc.add_heading("7. 13-Arm Component Ablation & Risk-Aversion Dynamics", level=1)
    
    img_f15 = 'full_doc_report/figures/F15_Complete_13Arm_Ablation_ReMedFiLM.png'
    if os.path.exists(img_f15):
        doc.add_picture(img_f15, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 15: 13-Arm Component Ablation and Safety Harm-Reduction Dynamics.").font.size = Pt(8)

    doc.add_paragraph(
        "Ablation findings on ROUTER_DEVELOPMENT (N=4,957):\n"
        "• Arm A1 (Unconditional Always-Refine): Degrades segmentation in 42.7% of all cases (2,115 cases).\n"
        "• Arm A7 (Learned Benefit Router B_phi): Reduces harm rate to 33.3% of routed crops (8.31% all-population).\n"
        "• Arm A8 (ReMedFiLM Full Assembly with S_omega): Further eliminates 22 harmful activations, raising mean routed delta to +0.75 pp and cutting all-population harm to 7.87%.\n"
        "• Arm F1 (Alpha-Blending): Results in -3.26 pp degradation due to blurred transition borders, validating ReMedFiLM's direct spatial canvas insertion."
    )

    # Section 8: Multi-Seed Reproducibility & Robustness
    doc.add_heading("8. Reproducibility, Environmental Stress & Complexity Trade-Off", level=1)
    
    img_f17 = 'full_doc_report/figures/F17_Seed_Reproducibility_ReMedFiLM.png'
    if os.path.exists(img_f17):
        doc.add_picture(img_f17, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 17: Multi-Seed Reproducibility Analysis (Seeds 42, 123, 3407) across Shared Global Backbone.").font.size = Pt(8)

    img_f18 = 'full_doc_report/figures/F18_Robustness_Perturbation_ReMedFiLM.png'
    if os.path.exists(img_f18):
        doc.add_picture(img_f18, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 18: Domain-Dependent Robustness under Acquisition Noise and Environmental Perturbations.").font.size = Pt(8)

    img_f19 = 'full_doc_report/figures/FIG_Accuracy_Compute_ReMedFiLM_V7.png'
    if os.path.exists(img_f19):
        doc.add_picture(img_f19, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 19: Computational Complexity, Pareto Frontier, and Latency Accounting.").font.size = Pt(8)

    doc.add_paragraph(
        "Latency & Compute Disclosures:\n"
        "• GlobalMedFiLM forward latency: 16.4 ms per image (31.55 GMACs).\n"
        "• ReMedFiLM full pipeline latency: 21.8 ms amortized across all cases; 26.5 ms on routed cases (+10.1 ms overhead for dynamic ROI cropping, router scoring, and spatial insertion).\n"
        "• Gaussian noise on KUB plain radiographs causes acute -36.36 pp degradation, revealing sensitivity to radiographic acquisition noise."
    )

    # Section 9: Supported Claims vs Pending Research Milestones
    doc.add_heading("9. Supported Scientific Claims vs. Documented Evidence Gaps", level=1)
    t9 = doc.add_table(rows=9, cols=3)
    t9.alignment = WD_TABLE_ALIGNMENT.CENTER
    t9_data = [
        ["Research Investigation", "Scientific Status", "Documented Evidence & Critical Guardrail"],
        ["ReMedFiLM Proposed Assembly", "SUPPORTED", "4.84M composed architecture (G + B_phi + R_psi + S_omega); achieves 83.79% VAL808 Dice (+0.28 pp dev mean)."],
        ["Risk-Averse Harm Reduction", "SUPPORTED", "Learned routing cuts refinement harm from 42.7% (A1) down to 7.87% (A8 on development cohort)."],
        ["Anatomical Subclass Gains", "SUPPORTED", "Statistically verified improvements on Bladder Stones (+1.46 pp) and Ureteric Stones (+1.06 pp)."],
        ["Stone-Free Negative Control Fragility", "MATERIAL FAILURE", "14/14 false positive detections on normal radiographs (Dice 0.000); phantom stone hallucination."],
        ["C1 Causal FiLM Attribution", "MISSING EVIDENCE", "0 of 6 planned paired C1 runs completed; causal FiLM attribution remains an active research frontier."],
        ["C2 Causal Component Attribution", "MISSING EVIDENCE", "Component ablations evaluated in-sample on ROUTER_DEVELOPMENT; causal held-out validation pending."],
        ["C3 24-Cell Matched Matrix", "MISSING EVIDENCE", "0 of 24 genuine matched multi-seed baseline cells completed; comparative claims restricted to Phase 21."],
        ["Untouched External Test Status", "EXPOSED HISTORICALLY", "External cohorts (CVC, BrEaST, Stones) were retrospectively evaluated; new independent validation pending."]
    ]
    for r_i, r_data in enumerate(t9_data):
        bg = "FFF5F5" if "FAILURE" in r_data[1] else ("F7FAFC" if "MISSING" in r_data[1] else ("1B365D" if r_i == 0 else "F0FFF4"))
        for c_i, v in enumerate(r_data):
            cell = t9.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i == 1 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_background(cell, bg)
            p.runs[0].font.size = Pt(7.5)
            if r_i == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif "FAILURE" in r_data[1]:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xC5, 0x30, 0x30)
            elif "SUPPORTED" in r_data[1]:
                p.runs[0].font.color.rgb = RGBColor(0x27, 0x67, 0x49)
            set_cell_margins(cell, 40, 40, 50, 50)

    # Section 10: Conclusion
    doc.add_heading("10. Conclusion & Publication Sign-Off", level=1)
    doc.add_paragraph(
        "ReMedFiLM establishes that selective, risk-averse secondary refinement overcomes the fundamental hazard of unconstrained multi-scale segmentation (reducing harm from 42.7% to 7.87%) while maintaining an ultra-compact 4.84M parameter footprint. When submitting to top-tier biomedical computing venues (IEEE TMI / Medical Image Analysis), authors must maintain complete transparency regarding normal-radiograph false positive rates and emphasize that causal FiLM attribution (C1) and 24-cell matched matrices (C3) remain prospective milestones. All source code, model checkpoints, prediction masks, and numerical evaluation matrices are archived in full_doc_report for verifiable replication."
    )

    out_docx = 'full_doc_report/ReMedFiLM_Complete_Scientific_Report_V7.docx'
    doc.save(out_docx)
    print(f'Successfully generated V7 DOCX: {out_docx}')

if __name__ == '__main__':
    build_v7_docx()
