"""
Build RA-MedFiLM-BARR Complete Scientific Results Master Report V5 in DOCX format.
Upgrades:
- Definitive V5 Methodology Figure (FIG01_FULL_RA_MedFiLM_BARR_Methodology_V5.png)
- Explicit proposed model framing: FULL RA-MedFiLM-BARR (composed 4.84M architecture)
- Exact mathematical equations: FiLM modulation, utility threshold, spatial fusion
- Staged freeze training strategy (no joint backprop)
- Preserves all 16 internal qualitative cases, external stress test, 13-arm ablation, 3-seed reproducibility, and negative disclosures
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

def build_v5_docx():
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)
        
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(3)
    
    # Title
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(0)
    tp.paragraph_format.space_after = Pt(2)
    tr = tp.add_run("RA-MedFiLM-BARR: Complete Scientific Results Master Report (V5)")
    tr.font.size = Pt(20)
    tr.font.bold = True
    tr.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(8)
    sr = sp.add_run("Risk-Averse Medical Feature-wise Linear Modulation with Boundary-Aware Residual Refinement (ReMedFiLM): Staged Modular Architecture, Multimodal Segmentation Atlas & Reproducibility Audit")
    sr.font.size = Pt(10.5)
    sr.font.italic = True
    sr.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)
    
    # Metadata Table
    meta_table = doc.add_table(rows=2, cols=4)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    hdrs = ["Proposed Method", "Internal Benchmark", "Historical External", "Audit Status"]
    vals = ["FULL RA-MedFiLM-BARR (4.84M)", "VAL808 (4 Heterogeneous Domains)", "EXTERNAL884 (3 Cohorts)", "V5 Publication Verified"]
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
        set_cell_margins(c_h, 50, 50, 70, 70)
        set_cell_margins(c_v, 50, 50, 70, 70)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 1
    doc.add_heading("1. Executive Summary & Proposed System Definition", level=1)
    p = doc.add_paragraph()
    p.add_run("The primary proposed architecture in this research program is ").font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    p.add_run("FULL RA-MedFiLM-BARR").bold = True
    p.add_run(" (historically designated ReMedFiLM in preliminary design milestones). FULL RA-MedFiLM-BARR is a composed four-stage modular inference system totaling ")
    p.add_run("4,837,420 parameters").bold = True
    p.add_run(" (4.84M). It pairs an ultra-efficient task-conditioned global segmenter (")
    p.add_run("GlobalMedFiLM").bold = True
    p.add_run(", G, 3.52M params) with a Boundary-Aware Residual Refinement pipeline comprising an empirical Benefit Router (")
    p.add_run("B_phi").bold = True
    p.add_run(", 36.8K params), a dedicated crop-trained Regional Refiner (")
    p.add_run("R_psi").bold = True
    p.add_run(", 1.28M params), and a Post-Safety Gate (")
    p.add_run("S_omega").bold = True
    p.add_run(", 1.22K params).")
    
    p2 = doc.add_paragraph()
    p2.add_run("Key Methodological Highlights & Disclosures:").bold = True
    doc.add_paragraph("• Staged Modular Assembly: The full model is NOT trained end-to-end with joint backpropagation. Components are trained in four sequential, isolated phases with frozen interfaces, introducing zero wrapper parameters and preventing cross-module gradient interference.")
    doc.add_paragraph("• Risk-Averse Routing Principle: Unconstrained secondary refinement is fundamentally unsafe, causing a 42.7% harmful activation rate (Arm A1). Learned benefit routing and post-safety gating suppress unpromising updates, elevating routed delta Dice to +0.75 pp (Arm A8).")
    doc.add_paragraph("• Material Negative Disclosures: Retrospective external testing reveals severe domain shift, including a 14/14 false-positive detection rate on stone-free radiographs (Dice 0.000). Noise sensitivity on plain radiographs is acute (-36.36 pp under Gaussian noise). Causal attribution studies (C1, C2, C3) remain future milestones.")

    # Section 2: V5 Architecture
    doc.add_heading("2. Canonical Architecture & Mathematical Formulation (V5)", level=1)
    p = doc.add_paragraph("Figure 1 depicts the complete V5 methodology, detailing multi-domain input conditioning, the four-component inference pipeline, the three runtime execution branches, and the staged training strategy.")
    
    fig1_png = 'full_doc_report/figures/FIG01_FULL_RA_MedFiLM_BARR_Methodology_V5.png'
    if os.path.exists(fig1_png):
        doc.add_picture(fig1_png, width=Inches(6.8))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run("Figure 1: Complete Methodology of FULL RA-MedFiLM-BARR (Proposed 4.84M Parameter Assembly). (A) Multi-domain inputs. (B) Core inference pipeline: GlobalMedFiLM G, Benefit Router B_phi, Regional Refiner R_psi, and Safety Gate S_omega with three canonical execution outcomes. (C) Staged freeze training strategy.")
        r.font.size = Pt(8)
        r.font.italic = True

    # Mathematical details
    doc.add_paragraph("Mathematical Formulation & Execution Mechanics:").bold = True
    doc.add_paragraph("1. FiLM Task Modulation: Given task t in {0:ISIC, 1:BUSI, 2:KVASIR, 3:KUB}, task embedding e_t = E(t) in R^32 modulates feature activations at 5 decoder/bridge sites: F_hat = (1 + tanh(gamma_raw(e_t))) * F + tanh(beta_raw(e_t)). Zero initialization ensures pure identity mapping at epoch 0.")
    doc.add_paragraph("2. ROI Proposal: Candidate bounding box window is proposed if any p_global >= 0.30, followed by 1.50x center-preserving expansion. If no foreground exists, the system triggers FORCED_SKIP -> p_global.")
    doc.add_paragraph("3. Benefit Routing: B_phi predicts paired gain delta_hat_final from 218 features. Action utility U = delta_hat_final - (1/4) * (1051648 / 10270749). If U < tau_C8_final (~ -0.024358), execution triggers SKIP_GLOBAL -> p_global (Refiner and Safety bypassed).")
    doc.add_paragraph("4. Regional Refinement & Fusion: R_psi processes 4-channel crops [RGB, p_global_crop] (256x256), outputting residual logits delta_l_roi. Candidate mask is p_cand_crop = sigmoid(logit(p_global_crop) + delta_l_roi). Fused deterministically into global canvas (NO alpha blending).")
    doc.add_paragraph("5. Post-Safety Gate: S_omega evaluates 20 comparative features. Refinement is adopted (EXECUTE_THEN_ACCEPT) iff P(safety) >= 0.50; otherwise fails closed (EXECUTE_THEN_REJECT -> p_global fallback).")

    # Section 3: Dataset Summary
    doc.add_heading("3. Dataset Organization & Benchmark Protocol", level=1)
    doc.add_paragraph("Table 1 summarizes cohort sizes across the four validated modalities. Each task formulates binary foreground segmentation. In KUB-StoneX, patient-level grouping is strictly enforced, and full-field radiographs are distinguished from cropped ROI patches.")
    
    t1 = doc.add_table(rows=6, cols=6)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1_data = [
        ["Domain / Dataset", "Modality", "Foreground Target", "TRAIN5832", "VAL808", "Historical TEST1683"],
        ["ISIC 2018", "Dermoscopy", "Cutaneous Pigmented Lesion", "2,594", "357", "735"],
        ["BUSI-WHU", "Breast Ultrasound", "Benign & Malignant Masses", "610", "84", "174"],
        ["Kvasir-SEG", "Colonoscopy", "Gastrointestinal Mucosal Polyp", "632", "87", "216"],
        ["KUB-StoneX", "Abdominal Radiography", "Kidney, Ureteric & Bladder Stones", "1,996", "280", "558"],
        ["Total Pooled", "4 Heterogeneous Modalities", "Binary Foreground per Task", "5,832", "808", "1,683"]
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
                p.runs[0].font.size = Pt(7.5)
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 5:
                set_cell_background(cell, "D9E2EC")
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(7.5)
            else:
                set_cell_background(cell, "F8FAFC" if r_i % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 45, 45, 60, 60)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 4: Internal Model Comparison
    doc.add_heading("4. Internal Six-Model Comparative Benchmark (VAL808)", level=1)
    p = doc.add_paragraph("Table 2 benchmarks FULL RA-MedFiLM-BARR and its internal backbone GlobalMedFiLM against five external baselines on VAL808.")
    
    t2 = doc.add_table(rows=8, cols=8)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2_data = [
        ["Model Architecture", "Params", "GMACs", "Macro Dice", "ISIC Dice", "BUSI Dice", "KVASIR Dice", "KUB Dice"],
        ["U-Net (Standard)", "7.76M", "46.14", "0.7878", "0.8553", "0.8198", "0.7552", "0.7211"],
        ["Attention U-Net", "7.85M", "47.22", "0.7890", "0.8617", "0.8277", "0.7710", "0.6958"],
        ["U-Net++", "9.16M", "137.94", "0.7920", "0.8601", "0.8163", "0.7710", "0.7207"],
        ["DeepLabV3+", "40.35M", "69.14", "0.8277", "0.8853", "0.8669", "0.8197", "0.7387"],
        ["Transformer / MiT U-Net", "16.35M", "99.10", "0.8224", "0.8871", "0.8640", "0.8133", "0.7252"],
        ["GlobalMedFiLM (Internal Backbone)", "3.52M", "31.55", "0.8351", "0.8972", "0.8588", "0.8202", "0.7641"],
        ["FULL RA-MedFiLM-BARR (Proposed)", "4.84M", "32.44*", "0.8379", "0.8982", "0.8589", "0.8210", "0.7734"]
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
            set_cell_margins(cell, 45, 45, 60, 60)
            
    doc.add_paragraph("*Note: FULL RA-MedFiLM-BARR GMACs reflect expected conditional execution under Arm A8 budget (32.44 GMACs). Paired bootstrap CIs against DeepLabV3+ cross zero on KVASIR and macro Dice; blanket statistical significance over DeepLabV3+ is not asserted.").paragraph_format.space_after = Pt(6)

    # Section 5: Subgroup Analysis
    doc.add_heading("5. Clinical Subgroup Performance Profile", level=1)
    doc.add_paragraph("Table 3 details performance across 8 verified clinical and morphological subgroups. FULL BARR achieves marked improvements on Bladder Stones (+1.46 pp) and Ureteric Stones (+1.06 pp) while preventing false-positive dilation on benign breast lesions (0.00 pp shift).")
    
    t3 = doc.add_table(rows=10, cols=6)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3_data = [
        ["Domain", "Verified Subgroup / Category", "N", "Global Baseline", "FULL BARR", "Net Shift & Routing Behavior"],
        ["ISIC 2018", "Cutaneous Lesion (Task-Level)", "357", "0.8972", "0.8982", "+0.10 pp (99.2% pass-through)"],
        ["BUSI-WHU", "Benign Breast Mass", "60", "0.8601", "0.8601", "0.00 pp (100% harm-filtered)"],
        ["BUSI-WHU", "Malignant Breast Mass", "24", "0.8557", "0.8561", "+0.04 pp (gated acceptance)"],
        ["Kvasir-SEG", "Large Polyp (>= median area)", "44", "0.8438", "0.8439", "+0.01 pp (conservative lock)"],
        ["Kvasir-SEG", "Small/Sessile Polyp (< median)", "43", "0.7961", "0.7976", "+0.15 pp (border enhancement)"],
        ["KUB-StoneX", "Bladder Stone (Pelvic)", "144", "0.7339", "0.7486", "+1.46 pp (high beneficial routing)"],
        ["KUB-StoneX", "Kidney Stone (Renal)", "112", "0.7964", "0.7988", "+0.24 pp (conservative routing)"],
        ["KUB-StoneX", "Ureteric Stone (Abdominal)", "24", "0.7939", "0.8045", "+1.06 pp (fine target capture)"],
        ["VAL808 Macro", "Unified Multi-Domain Benchmark", "808", "0.8351", "0.8379", "+0.28 pp (p < 10^-4 Wilcoxon)"]
    ]
    for r_i, r_data in enumerate(t3_data):
        row_y = r_i
        bg = "D9E2EC" if r_i == 9 else ("1B365D" if r_i == 0 else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF"))
        for c_i, v in enumerate(r_data):
            cell = t3.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_background(cell, bg)
            p.runs[0].font.size = Pt(7.5)
            if r_i == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 9:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
            set_cell_margins(cell, 45, 45, 60, 60)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 6: Internal Qualitative Galleries (Figs 4-7 in report sequence)
    doc.add_heading("6. Four-Domain Qualitative Semantic Segmentation Galleries", level=1)
    doc.add_paragraph("All segmentation visualizations feature real prediction masks from the frozen validation cohort. Color scheme: True Positive (Green), False Positive (Red), False Negative (Blue) over native image context (alpha = 0.45).")
    
    # Embed Figs 1-4 from full_doc_report/figures/
    gallery_pairs = [
        ('full_doc_report/figures/fig1_isic_cases.png', 'Figure 4: ISIC 2018 Dermoscopy Qualitative Grid (Typical, High-Performing, Boundary-Challenging, Follicular Failure).'),
        ('full_doc_report/figures/fig2_busi_subclasses.png', 'Figure 5: BUSI-WHU Breast Ultrasound Qualitative Grid (Verified Benign vs Malignant Lesions).'),
        ('full_doc_report/figures/fig3_kvasir_cases.png', 'Figure 6: Kvasir-SEG Colonoscopy Qualitative Grid (Morphological Scales & Specular Glare Failure).'),
        ('full_doc_report/figures/fig4_kub_subclasses.png', 'Figure 7: KUB-StoneX Plain Radiographs across Verified Stone Sites (Bladder, Kidney, Ureteric). Full-field radiographs shown.')
    ]
    for g_path, g_cap in gallery_pairs:
        if os.path.exists(g_path):
            doc.add_picture(g_path, width=Inches(6.6))
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = cap.add_run(g_cap)
            r.font.size = Pt(8)
            r.font.italic = True

    # Section 7: External Retrospective Evaluation
    doc.add_heading("7. External Retrospective Evaluation & Material Negative Findings", level=1)
    doc.add_paragraph("Table 4 documents performance on EXTERNAL884 (CVC-ClinicDB: 612, BrEaST-Lesions-USG: 252, Stones: 20).")
    
    t4 = doc.add_table(rows=5, cols=8)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4_data = [
        ["External Cohort", "Analogue", "N", "Global Dice", "FULL Dice", "Δ (pp)", "Harm Rate", "Documented Transfer Vulnerability"],
        ["CVC-ClinicDB", "KVASIR", "612", "0.6866", "0.6897", "+0.318", "27.7%", "Moderate shift (-13.4 pp vs VAL)"],
        ["BrEaST-Lesions-USG", "BUSI", "252", "0.7078", "0.7081", "+0.028", "12.5%", "Acoustic shift (-15.1 pp vs VAL)"],
        ["Stones (Stone-Positive)", "KUB", "6", "0.2695", "0.2738", "+0.429", "0.0%", "Severe transfer degradation"],
        ["Stones (Stone-Free Neg.)", "KUB", "14", "0.0000", "0.0000", "0.000", "N/A", "14 / 14 FALSE POSITIVE DETECTIONS"]
    ]
    for r_i, r_data in enumerate(t4_data):
        bg = "FFECEC" if r_i == 4 else ("1B365D" if r_i == 0 else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF"))
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
            elif r_i == 4:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0x99, 0x00, 0x00)
            set_cell_margins(cell, 45, 45, 55, 55)

    doc.add_paragraph("Material Finding: On 14 stone-free negative radiographs, GlobalMedFiLM and BARR both produced false-positive calcification detections across all 14 images (Dice 0.000). Safety gating rejected 1 of 3 routed proposals, adopting 2 false-positive masks. This proves that post-safety gating does NOT eliminate false positive hallucination on completely stone-free imagery.").paragraph_format.space_after = Pt(6)

    # Embed External Qualitative Gallery
    ext_g = 'full_doc_report/figures/fig_external_qualitative_gallery.png'
    if os.path.exists(ext_g):
        doc.add_picture(ext_g, width=Inches(6.6))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 8: External Qualitative Gallery (Beneficial, Harmful, Rejected, Non-Selected, and Stone-Free False-Positive Cases).").font.size = Pt(8)

    # Section 8: Progression & 13-Arm Ablation
    doc.add_heading("8. 13-Arm Component Ablation & Progression Dynamics", level=1)
    doc.add_paragraph("Table 5 summarizes the Phase 28 13-arm ablation matrix (A0–A8, R1–R3, F1). Always-refine (A1) produces 42.7% harmful activations. Learned routing (A7) cuts harm to 33.3%. Post-safety (A8) eliminates 34 negative outliers, elevating routed delta to +0.75 pp. Contrast A8 vs A7 95% CI spans zero, confirming that this increment is descriptive.")
    
    t5 = doc.add_table(rows=14, cols=7)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
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
    for r_i, r_data in enumerate(t5_data):
        bg = "D9E2EC" if r_i == 9 else ("1B365D" if r_i == 0 else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF"))
        for c_i, v in enumerate(r_data):
            cell = t5.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_background(cell, bg)
            p.runs[0].font.size = Pt(7)
            if r_i == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif r_i == 9:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
            set_cell_margins(cell, 35, 35, 45, 45)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 9: Reproducibility, Robustness & Efficiency
    doc.add_heading("9. Reproducibility, Robustness & Pareto Efficiency", level=1)
    doc.add_paragraph("Three-Seed Reproducibility (VAL808): Seeds 42, 123, 3407 yield 0.837862 ± 0.00004 Dice across a shared pre-trained GlobalMedFiLM backbone. Variance reflects refiner and router initialization stability, not independent end-to-end retrainings.")
    doc.add_paragraph("Systematic Perturbation Sensitivity: High Gaussian noise on KUB plain radiographs causes acute degradation (-36.36 pp), whereas dermoscopy (-3.15 pp) and endoscopy (-6.04 pp) remain robust.")
    doc.add_paragraph("Computational Complexity: FULL BARR requires 4.84M parameters and 32.44 GMACs (expected conditional execution), achieving 67.2% compute reduction compared to vision transformers (MiT U-Net: 99.10 GMACs). Single-image latency on RTX 3060 Ti is 15.72 ms (skipped path) to 18.89 ms (executed path).")

    # Section 10: Supported Claims vs Unresolved Frontiers
    doc.add_heading("10. Supported Scientific Claims vs. Critical Evidence Gaps", level=1)
    t8 = doc.add_table(rows=9, cols=3)
    t8.alignment = WD_TABLE_ALIGNMENT.CENTER
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
    for r_i, r_data in enumerate(t8_data):
        bg = "FFF5F5" if "FAILURE" in r_data[1] else ("F7FAFC" if "MISSING" in r_data[1] else ("1B365D" if r_i == 0 else "F0FFF4"))
        for c_i, v in enumerate(r_data):
            cell = t8.cell(r_i, c_i)
            cell.text = v
            p = cell.paragraphs[0]
            if c_i == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
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
            set_cell_margins(cell, 45, 45, 55, 55)

    # Section 11: Conclusion
    doc.add_heading("11. Conclusion & Scientific Submission Guidance", level=1)
    p_end = doc.add_paragraph()
    p_end.add_run("The RA-MedFiLM-BARR research lifecycle establishes that task-conditioned FiLM representations paired with selective, risk-averse residual refinement achieve robust multi-domain segmentation performance without the excessive computational overhead of large vision transformers. However, submission to premier journals (IEEE TMI / Medical Image Analysis) requires transparent disclosure of external transfer vulnerabilities, specifically the stone-free false positive detection rate, and explicit acknowledgment that causal FiLM attribution (C1) and 24-cell matched baseline comparisons (C3) remain future experimental milestones. The complete code, checkpoints, prediction masks, and numerical evidence are archived for independent scientific verification.")
    
    out_docx = 'full_doc_report/RA_MedFiLM_BARR_Complete_Scientific_Results_V5.docx'
    doc.save(out_docx)
    print(f'Saved V5 DOCX: {out_docx}')

build_v5_docx()
