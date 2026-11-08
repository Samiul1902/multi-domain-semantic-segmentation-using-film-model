"""
Script to build the definitive, publication-grade 20-page Master Scientific Report V5 in PDF format:
ReMedFiLM_Complete_Scientific_Report_V6.pdf
Uses PyMuPDF (fitz) with clean typography, page tracking, compressed graphics (<50MB total),
integrating the official V5 Methodology Figure and rigorous evidence disclosures.
"""

import os
import fitz

def build_v5_pdf():
    pdf_out = 'full_doc_report/ReMedFiLM_Complete_Scientific_Report_V6.pdf'
    doc = fitz.open()
    
    # Dimensions: Standard Letter (612 x 792 pt)
    pw, ph = 612, 792
    mx, my = 36, 36
    cw = pw - 2 * mx
    
    TOTAL_PAGES = 20
    
    def decorate(p, p_num):
        # Header
        p.draw_line(fitz.Point(mx, 26), fitz.Point(pw - mx, 26), color=(0.11, 0.21, 0.36), width=1)
        p.insert_text(fitz.Point(mx, 20), "ReMedFiLM: Complete Scientific Results Master Report (V6)", fontsize=7.5, color=(0.11, 0.21, 0.36))
        p.insert_text(fitz.Point(pw - mx - 120, 20), "Evidence & Reproducibility Atlas", fontsize=7.5, color=(0.3, 0.3, 0.3))
        # Footer
        p.draw_line(fitz.Point(mx, ph - 24), fitz.Point(pw - mx, ph - 24), color=(0.7, 0.7, 0.7), width=0.5)
        p.insert_text(fitz.Point(mx, ph - 14), "Confidential Medical Image Computing Research Report | Quarantined VAL808 Benchmark Protocol", fontsize=7.5, color=(0.4, 0.4, 0.4))
        p.insert_text(fitz.Point(pw - mx - 50, ph - 14), f"Page {p_num} of {TOTAL_PAGES}", fontsize=7.5, color=(0.2, 0.2, 0.2))

    # =========================================================
    # PAGE 1: COVER & EXECUTIVE SUMMARY
    # =========================================================
    p1 = doc.new_page(width=pw, height=ph)
    # Header Banner
    p1.draw_rect(fitz.Rect(mx, 38, pw - mx, 130), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
    p1.insert_text(fitz.Point(mx + 15, 65), "ReMedFiLM: Complete Scientific Results Master Report", fontsize=16, color=(1, 1, 1))
    p1.insert_text(fitz.Point(mx + 15, 84), "Version 5.0 — Publication-Grade Methodology, Staged Assembly & Scientific Audit", fontsize=10.5, color=(0.85, 0.90, 0.98))
    p1.insert_text(fitz.Point(mx + 15, 102), "Risk-Averse Medical Feature-wise Linear Modulation with Boundary-Aware Residual Refinement (ReMedFiLM)", fontsize=8.5, color=(0.75, 0.82, 0.92))
    p1.insert_text(fitz.Point(mx + 15, 118), "Benchmark Protocol: VAL808 Internal | EXTERNAL884 Retrospective | TEST1683 Historical", fontsize=8, color=(0.65, 0.75, 0.85))

    # Meta Grid
    mb = fitz.Rect(mx, 138, pw - mx, 185)
    p1.draw_rect(mb, color=(0.8, 0.85, 0.9), fill=(0.95, 0.97, 0.99))
    p1.insert_text(fitz.Point(mx + 12, 154), "Primary Proposed Model: ReMedFiLM (FULL RA-MedFiLM-BARR) (Composed 4.84M Parameters: G + B_phi + R_psi + S_omega)", fontsize=8.5, color=(0.11, 0.21, 0.36))
    p1.insert_text(fitz.Point(mx + 12, 168), "Internal Backbone G: GlobalMedFiLM (3.52M params, 0.8351 macro Dice) | FULL Model: 0.8379 macro Dice (+0.28 pp)", fontsize=8, color=(0.11, 0.21, 0.36))
    p1.insert_text(fitz.Point(mx + 12, 180), "Disclosed Limitations: 14/14 Stone-Free False Positives | Noise Sensitivity (-36.4 pp) | C1/C2/C3 Causal Studies Pending", fontsize=8, color=(0.7, 0.1, 0.1))

    # Section 1: Executive Summary
    y = 200
    p1.insert_text(fitz.Point(mx, y), "1. Executive Summary & Proposed System Definition", fontsize=12, color=(0.11, 0.21, 0.36))
    p1.draw_line(fitz.Point(mx, y + 4), fitz.Point(pw - mx, y + 4), color=(0.11, 0.21, 0.36), width=1)
    
    text_s1 = (
        "Multi-domain medical image segmentation requires models to generalize across drastically divergent imaging modalities "
        "(dermoscopy, ultrasound, endoscopy, radiography) while preserving millimeter-accurate target contours. Conventional monolithic "
        "networks trained jointly across heterogeneous tasks suffer from negative cross-task interference. Conversely, unconstrained two-stage "
        "or cascading networks frequently hallucinate spurious lesions under ambiguous acoustic attenuation or radiographic noise.\n\n"
        "The primary proposed architecture in this research program is ReMedFiLM (FULL RA-MedFiLM-BARR) (historically designated ReMedFiLM in early development). "
        "ReMedFiLM (FULL RA-MedFiLM-BARR) is a composed four-stage modular inference system totaling 4,837,420 parameters (4.84M). It pairs an ultra-efficient "
        "task-conditioned global segmenter (GlobalMedFiLM, G, 3.52M params) with a Boundary-Aware Residual Refinement pipeline comprising an empirical "
        "Benefit Router (B_phi, 36.8K params), a dedicated crop-trained Regional Refiner (R_psi, 1.28M params), and a Post-Safety Gate (S_omega, 1.22K params).\n\n"
        "Key Methodological Highlights & Disclosures:\n"
        "  1. Staged Modular Assembly: The full model is NOT trained end-to-end with joint backpropagation. Components are trained in four sequential, "
        "isolated phases with frozen interfaces, introducing zero wrapper parameters and preventing cross-module gradient interference.\n"
        "  2. Risk-Averse Routing Principle: Unconstrained secondary refinement is fundamentally unsafe, causing a 42.7% harmful activation rate (Arm A1). "
        "Learned benefit routing and post-safety gating suppress unpromising updates, elevating routed delta Dice to +0.75 pp (Arm A8).\n"
        "  3. Material Negative Disclosures: Retrospective external testing reveals severe domain shift, including a 14/14 false-positive detection rate "
        "on stone-free radiographs (Dice 0.000). Noise sensitivity on plain radiographs is acute (-36.36 pp under Gaussian noise). Causal attribution studies "
        "(C1, C2, C3) remain future milestones."
    )
    p1.insert_textbox(fitz.Rect(mx, y + 10, pw - mx, ph - 30), text_s1, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p1, 1)

    # =========================================================
    # PAGE 2: V5 METHODOLOGY FIGURE (FIG 1)
    # =========================================================
    p2 = doc.new_page(width=pw, height=ph)
    p2.insert_text(fitz.Point(mx, 45), "2. Canonical ReMedFiLM Methodology Architecture (V6 Definitive)", fontsize=12, color=(0.11, 0.21, 0.36))
    p2.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    
    img_v5 = 'full_doc_report/figures/FIG01_ReMedFiLM_Methodology_V6.png'
    if os.path.exists(img_v5):
        # Embed large high-res landscape methodology diagram
        p2.insert_image(fitz.Rect(mx, 55, pw - mx, 410), filename=img_v5)
        
    p2.insert_text(fitz.Point(mx, 420), "Figure 1: Complete Methodology of ReMedFiLM (FULL RA-MedFiLM-BARR) (Proposed 4.84M Parameter Assembly).", fontsize=8, color=(0.3, 0.3, 0.3))
    
    text_v5_desc = (
        "Figure 1 Architecture Components & Execution Details:\n"
        "  * Panel A (Multi-Domain Input): Inputs x in R^{1x3x512x512} paired with discrete task identity t in {0:ISIC, 1:BUSI, 2:KVASIR, 3:KUB}. "
        "Embedding generator E(t) produces e_t in R^32. Task formulation is strictly single-class binary foreground per task.\n"
        "  * Panel B (FULL Architecture): (1) GlobalMedFiLM (G, 3.52M params) modulates bridge and 4 decoder stages with FiLM: "
        "F_hat = (1 + tanh(gamma_raw(e_t))) * F + tanh(beta_raw(e_t)). Zero-initialization guarantees pure identity at epoch 0. (2) ROI Proposal: "
        "Extracts bounding box where p_global >= 0.30, expanded by 1.50x. If no foreground exists, triggers FORCED_SKIP -> p_global. (3) Benefit Router "
        "(B_phi, 36.8K params): Regresses expected paired gain delta_hat from 218 features. Evaluates utility U = delta_hat - lambda*C. If U < tau_C8_final, "
        "triggers SKIP_GLOBAL -> p_global. (4) Regional Refiner (R_psi, 1.28M params): Narrowed U-Net processing 4-channel crops [RGB, p_global_crop], "
        "predicting residual logits delta_l_roi. Fused deterministically into canvas (NO alpha blending). (5) Post-Safety Gate (S_omega, 1.22K params): "
        "Evaluates 20 comparative divergence features. Adopts candidate (EXECUTE_THEN_ACCEPT) iff P(safe) >= 0.50; else fails closed (EXECUTE_THEN_REJECT -> p_global).\n"
        "  * Panel C (Staged Training Strategy): Four isolated training phases without joint backpropagation, ensuring deterministic assembly."
    )
    p2.insert_textbox(fitz.Rect(mx, 435, pw - mx, ph - 30), text_v5_desc, fontsize=8, color=(0.15, 0.15, 0.15), lineheight=1.2)
    decorate(p2, 2)

    # =========================================================
    # PAGE 3: DATASET DESIGN & PROTOCOLS
    # =========================================================
    p3 = doc.new_page(width=pw, height=ph)
    p3.insert_text(fitz.Point(mx, 45), "3. Dataset Protocol & Clinical Grouping Structure", fontsize=12, color=(0.11, 0.21, 0.36))
    p3.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    
    img_proto = 'full_doc_report/figures/fig_dataset_protocol.png'
    if os.path.exists(img_proto):
        p3.insert_image(fitz.Rect(mx, 55, pw - mx, 320), filename=img_proto)
    p3.insert_text(fitz.Point(mx, 328), "Figure 2: Multi-Domain Benchmark Protocol, Partitions, and Task Foregrounds.", fontsize=8, color=(0.3, 0.3, 0.3))

    p3.insert_text(fitz.Point(mx, 345), "Table 1: Cohort Partitioning, Foreground Targets, and Patient Grouping Status", fontsize=9.5, color=(0.11, 0.21, 0.36))
    
    t1_y = 360
    t1_w = [85, 95, 120, 65, 55, 120]
    t1_hdrs = ["Domain", "Modality", "Foreground Target", "TRAIN5832", "VAL808", "Patient Grouping"]
    cur_x = mx
    for i, h in enumerate(t1_hdrs):
        p3.draw_rect(fitz.Rect(cur_x, t1_y, cur_x + t1_w[i], t1_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p3.insert_text(fitz.Point(cur_x + 3, t1_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t1_w[i]
        
    t1_rows = [
        ["ISIC 2018", "Dermoscopy", "Pigmented Skin Lesion", "2,594", "357", "Not recorded in source"],
        ["BUSI-WHU", "Breast US", "Benign / Malignant Mass", "610", "84", "Patient registry matched"],
        ["Kvasir-SEG", "Colonoscopy", "Mucosal Adenoma Polyp", "632", "87", "Sequence unstratified"],
        ["KUB-StoneX", "Abdominal XR", "Kidney/Ureter/Bladder Stone", "1,996", "280", "Patient-level grouped"],
        ["Total Pooled", "4 Modalities", "Binary Foreground per Task", "5,832", "808", "Partition air-gapped"]
    ]
    for r_i, r_data in enumerate(t1_rows):
        row_y = t1_y + 18 + r_i * 16
        bg = (0.85, 0.89, 0.93) if r_i == 4 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p3.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t1_w[c_i], row_y + 16), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.11, 0.21, 0.36) if r_i == 4 else (0.1, 0.1, 0.1)
            p3.insert_text(fitz.Point(cur_x + 3, row_y + 11), v, fontsize=7, color=f_col)
            cur_x += t1_w[c_i]

    text_proto = (
        "Critical Task Definition & Subgroup Provenance:\n"
        "  * Binary Formulation: The model performs strictly single-class binary foreground segmentation per task. ISIC, BUSI, KVASIR, and KUB "
        "are task indices, not simultaneous output channels. In KUB, kidney, ureteric, and bladder stones are evaluation subgroups, not distinct labels.\n"
        "  * Full-Field vs ROI Representation: KUB-StoneX includes mixed representations: 873 full-field radiographs and 1,385 ROI patches. "
        "In Section 5, full-field radiographs are explicitly distinguished from cropped ROI instances.\n"
        "  * Independence Limits: While KUB-StoneX enforces strict patient-level splitting (preventing patient leakage across splits), ISIC and "
        "Kvasir-SEG lack patient identifiers in public manifests. Claims of complete patient-level independence must be qualified accordingly."
    )
    p3.insert_textbox(fitz.Rect(mx, 465, pw - mx, ph - 30), text_proto, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p3, 3)

    # =========================================================
    # PAGE 4: INTERNAL MODEL BENCHMARK (SIX MODELS)
    # =========================================================
    p4 = doc.new_page(width=pw, height=ph)
    p4.insert_text(fitz.Point(mx, 45), "4. Internal Six-Model Comparative Benchmark (VAL808)", fontsize=12, color=(0.11, 0.21, 0.36))
    p4.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    
    img_perf = 'full_doc_report/figures/fig_internal_performance_summary.png'
    if os.path.exists(img_perf):
        p4.insert_image(fitz.Rect(mx, 55, pw - mx, 320), filename=img_perf)
    p4.insert_text(fitz.Point(mx, 328), "Figure 3: Six-Model Comparative Distribution across Internal Domains (Phase 21 Benchmark).", fontsize=8, color=(0.3, 0.3, 0.3))

    p4.insert_text(fitz.Point(mx, 345), "Table 2: Unified Six-Model Primary Performance Matrix on Frozen VAL808", fontsize=9.5, color=(0.11, 0.21, 0.36))
    
    t2_y = 360
    t2_w = [110, 55, 60, 65, 60, 60, 60, 70]
    t2_hdrs = ["Model Architecture", "Params", "GMACs", "Macro Dice", "ISIC", "BUSI", "KVASIR", "KUB"]
    cur_x = mx
    for i, h in enumerate(t2_hdrs):
        p4.draw_rect(fitz.Rect(cur_x, t2_y, cur_x + t2_w[i], t2_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p4.insert_text(fitz.Point(cur_x + 3, t2_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t2_w[i]
        
    t2_rows = [
        ["U-Net (Standard)", "7.76M", "46.14", "0.7878", "0.8553", "0.8198", "0.7552", "0.7211"],
        ["Attention U-Net", "7.85M", "47.22", "0.7890", "0.8617", "0.8277", "0.7710", "0.6958"],
        ["U-Net++", "9.16M", "137.94", "0.7920", "0.8601", "0.8163", "0.7710", "0.7207"],
        ["DeepLabV3+", "40.35M", "69.14", "0.8277", "0.8853", "0.8669", "0.8197", "0.7387"],
        ["Transformer / MiT U-Net", "16.35M", "99.10", "0.8224", "0.8871", "0.8640", "0.8133", "0.7252"],
        ["GlobalMedFiLM (Internal Backbone)", "3.52M", "31.55", "0.8351", "0.8972", "0.8588", "0.8202", "0.7641"],
        ["ReMedFiLM (FULL RA-MedFiLM-BARR) (Proposed)", "4.84M", "32.44*", "0.8379", "0.8982", "0.8589", "0.8210", "0.7734"]
    ]
    for r_i, r_data in enumerate(t2_rows):
        row_y = t2_y + 18 + r_i * 16
        bg = (0.85, 0.89, 0.93) if r_i == 6 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p4.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t2_w[c_i], row_y + 16), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.11, 0.21, 0.36) if r_i == 6 else (0.1, 0.1, 0.1)
            p4.insert_text(fitz.Point(cur_x + 3, row_y + 11), v, fontsize=7, color=f_col)
            cur_x += t2_w[c_i]

    text_perf = (
        "Internal Performance Analysis & Statistical Caveats:\n"
        "  * GlobalMedFiLM establishes clear superiority over standard U-Net (+4.73 pp), Attention U-Net (+4.61 pp), and U-Net++ (+4.31 pp). "
        "Task-conditioned FiLM enables effective knowledge sharing across modalities without negative cross-task interference.\n"
        "  * Contrast with DeepLabV3+: While GlobalMedFiLM surpasses DeepLabV3+ in macro Dice (0.8351 vs 0.8277), DeepLabV3+ achieves slightly higher "
        "point performance on ultrasound (0.8669 vs 0.8588). Paired bootstrap confidence intervals on specific sub-domains span zero; claims of "
        "universal statistical significance over DeepLabV3+ are therefore scientifically unjustified.\n"
        "  * FULL BARR Gain: The addition of selective BARR refinement achieves 0.8379 macro Dice (+0.28 pp overall), driven primarily by "
        "substantial improvements on low-contrast abdominal radiographs (KUB: 0.7734 vs 0.7641, +0.93 pp domain shift)."
    )
    p4.insert_textbox(fitz.Rect(mx, 495, pw - mx, ph - 30), text_perf, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p4, 4)

    # =========================================================
    # PAGE 5: DOMAIN & SUBGROUP PERFORMANCE
    # =========================================================
    p5 = doc.new_page(width=pw, height=ph)
    p5.insert_text(fitz.Point(mx, 45), "5. Class, Subclass & Morphological Subgroup Evaluation", fontsize=12, color=(0.11, 0.21, 0.36))
    p5.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    
    img_sub = 'full_doc_report/figures/fig5_domain_subgroup_matrix.png'
    if os.path.exists(img_sub):
        p5.insert_image(fitz.Rect(mx, 55, pw - mx, 300), filename=img_sub)
    p5.insert_text(fitz.Point(mx, 308), "Figure 4: Domain Macro Performance (A) and Verified Clinical Subgroup Profile (B) on VAL808.", fontsize=8, color=(0.3, 0.3, 0.3))

    p5.insert_text(fitz.Point(mx, 325), "Table 3: Fine-Grained Subgroup Performance Breakdown across All 808 Validation Cases", fontsize=9.5, color=(0.11, 0.21, 0.36))
    
    t3_y = 340
    t3_w = [85, 135, 45, 75, 75, 125]
    t3_hdrs = ["Domain", "Verified Subgroup / Category", "N", "Global Baseline", "FULL BARR", "Net Shift & Routing Behavior"]
    cur_x = mx
    for i, h in enumerate(t3_hdrs):
        p5.draw_rect(fitz.Rect(cur_x, t3_y, cur_x + t3_w[i], t3_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p5.insert_text(fitz.Point(cur_x + 3, t3_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t3_w[i]
        
    t3_rows = [
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
    for r_i, r_data in enumerate(t3_rows):
        row_y = t3_y + 18 + r_i * 16
        bg = (0.85, 0.89, 0.93) if r_i == 8 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p5.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t3_w[c_i], row_y + 16), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.11, 0.21, 0.36) if r_i == 8 else (0.1, 0.1, 0.1)
            p5.insert_text(fitz.Point(cur_x + 3, row_y + 11), v, fontsize=7, color=f_col)
            cur_x += t3_w[c_i]

    text_sub = (
        "Subgroup Clinical Interpretation:\n"
        "  * Verified Benign Protection: In BUSI-WHU, benign fibroadenomas exhibit a net shift of 0.00 pp. The router and safety gate reject "
        "uncertain acoustic shadow updates, avoiding false positive dilation around circumscribed margins.\n"
        "  * Calculi Localization Gains: In KUB-StoneX, pelvic bladder stones (+1.46 pp) and small ureteric stones (+1.06 pp) achieve the largest "
        "gains in the entire study, confirming that boundary residual attention successfully separates dense calcifications from adjacent pelvic "
        "bone cortex and intestinal gas shadows."
    )
    p5.insert_textbox(fitz.Rect(mx, 505, pw - mx, ph - 30), text_sub, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p5, 5)

    # =========================================================
    # PAGES 6-9: FOUR INTERNAL SEGMENTATION GALLERIES
    # =========================================================
    # Page 6: ISIC
    p6 = doc.new_page(width=pw, height=ph)
    p6.insert_text(fitz.Point(mx, 45), "6. Qualitative Gallery: ISIC 2018 Cutaneous Dermoscopy", fontsize=12, color=(0.11, 0.21, 0.36))
    p6.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig1_isic_cases.png'):
        p6.insert_image(fitz.Rect(mx, 55, pw - mx, 480), filename='full_doc_report/figures/fig1_isic_cases.png')
    p6.insert_text(fitz.Point(mx, 490), "Figure 5: ISIC 2018 Dermoscopy Qualitative Segmentation (Typical, High-Performing, Boundary-Challenging, Follicular Failure).", fontsize=8, color=(0.3, 0.3, 0.3))
    text_g1 = (
        "Case Analysis (Overlay Color Code: TP = Green, FP = Red, FN = Blue, Alpha = 0.45):\n"
        "  * Row 1 (Typical Lesion, ID 1e2fcea...): Symmetrical nevus; Global Dice 0.934. BARR retains border alignment without dilating.\n"
        "  * Row 2 (High-Performing, ID 780038a...): High pigment contrast; Dice 0.993, IoU 0.985. Virtually zero false positive perimeter noise.\n"
        "  * Row 3 (Boundary-Challenging, ID 805b4a9...): Faint melanin transition. BARR recovers peripheral networks (Dice 0.795 -> 0.804, +0.90 pp).\n"
        "  * Row 4 (Follicular Failure, ID f949cba...): Severe occlusion by dense dark hairs. Model suffers boundary fragmentation (Dice 0.276 vs 0.248)."
    )
    p6.insert_textbox(fitz.Rect(mx, 505, pw - mx, ph - 30), text_g1, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p6, 6)

    # Page 7: BUSI
    p7 = doc.new_page(width=pw, height=ph)
    p7.insert_text(fitz.Point(mx, 45), "7. Qualitative Gallery: BUSI-WHU Breast Ultrasound Pathology", fontsize=12, color=(0.11, 0.21, 0.36))
    p7.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig2_busi_subclasses.png'):
        p7.insert_image(fitz.Rect(mx, 55, pw - mx, 480), filename='full_doc_report/figures/fig2_busi_subclasses.png')
    p7.insert_text(fitz.Point(mx, 490), "Figure 6: BUSI-WHU Sonography Qualitative Segmentation (Verified Benign vs Malignant Pathologies).", fontsize=8, color=(0.3, 0.3, 0.3))
    text_g2 = (
        "Case Analysis (Verified Pathology Registers):\n"
        "  * Row 1 (Benign High-Concordance, ID bba663c...): Circumscribed oval fibroadenoma. Global and BARR capture margin (Dice 0.967, IoU 0.935).\n"
        "  * Row 2 (Benign Acoustic Attenuation, ID b2964ec...): Posterior acoustic shadowing. BARR's router detects high uncertainty, failing closed "
        "and preventing catastrophic false-positive red dilation into acoustic dropouts (100% harm rejection across benign cases).\n"
        "  * Row 3 (Malignant High-Contrast, ID ca7d23d...): Infiltrating ductal carcinoma with micro-lobulated margins (Dice 0.950).\n"
        "  * Row 4 (Invasive Malignant, ID 78a5416...): Invasive tumor with blurred fascial planes; stable conservative contour (Dice 0.816)."
    )
    p7.insert_textbox(fitz.Rect(mx, 505, pw - mx, ph - 30), text_g2, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p7, 7)

    # Page 8: KVASIR
    p8 = doc.new_page(width=pw, height=ph)
    p8.insert_text(fitz.Point(mx, 45), "8. Qualitative Gallery: Kvasir-SEG Endoscopic Mucosal Lesions", fontsize=12, color=(0.11, 0.21, 0.36))
    p8.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig3_kvasir_cases.png'):
        p8.insert_image(fitz.Rect(mx, 55, pw - mx, 480), filename='full_doc_report/figures/fig3_kvasir_cases.png')
    p8.insert_text(fitz.Point(mx, 490), "Figure 7: Kvasir-SEG Colonoscopy Qualitative Segmentation (Morphological Scale & Reflection Artifacts).", fontsize=8, color=(0.3, 0.3, 0.3))
    text_g3 = (
        "Case Analysis (Morphological Area Quantiles):\n"
        "  * Row 1 (Large Pedunculated Adenoma, ID 58a2693...): Dominant polyp; Dice 0.983, IoU 0.966. Excellent mucosal margin recovery.\n"
        "  * Row 2 (Medium / Typical Polyp, ID a859759...): Adenoma positioned along mucosal wall fold; Dice 0.892.\n"
        "  * Row 3 (Small / Sessile Polyp, ID b53f741...): Low-profile flat adenoma (< median area). Subtle edge refinement yields +0.15 pp net benefit.\n"
        "  * Row 4 (Specular Glare Failure, ID 1f91550...): Severe colonoscope LED flare saturates sensor. Model misses faint lesion under glare (Dice 0.131)."
    )
    p8.insert_textbox(fitz.Rect(mx, 505, pw - mx, ph - 30), text_g3, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p8, 8)

    # Page 9: KUB
    p9 = doc.new_page(width=pw, height=ph)
    p9.insert_text(fitz.Point(mx, 45), "9. Qualitative Gallery: KUB-StoneX Plain Abdominal Radiographs", fontsize=12, color=(0.11, 0.21, 0.36))
    p9.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig4_kub_subclasses.png'):
        p9.insert_image(fitz.Rect(mx, 55, pw - mx, 480), filename='full_doc_report/figures/fig4_kub_subclasses.png')
    p9.insert_text(fitz.Point(mx, 490), "Figure 8: KUB-StoneX Plain Radiography (Verified Stone Sites: Bladder, Kidney, Ureteric). Note: Full-field radiographs.", fontsize=8, color=(0.3, 0.3, 0.3))
    text_g4 = (
        "Case Analysis (Verified Radiographic Calculi Sites):\n"
        "  * Row 1 (Bladder Stone, ID 8f34020...): Pelvic cavity calculus. BARR delivers a massive +2.69 pp gain over Global (Dice 0.930 vs 0.903).\n"
        "  * Row 2 (Kidney Stone, ID 80e180b...): Upper calyx nephrolithiasis. High-precision detection (Dice 0.929) without false positives over ribs.\n"
        "  * Row 3 (Ureteric Stone, ID 9cb660e...): Small radio-opaque calculus projected over sacroiliac joint (Dice 0.930 vs 0.917, +1.26 pp).\n"
        "  * Row 4 (Punctate Calculus Failure, ID 5015703...): Sub-centimeter calculus completely obscured by bowel gas. Complete false negative failure."
    )
    p9.insert_textbox(fitz.Rect(mx, 505, pw - mx, ph - 30), text_g4, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p9, 9)

    # =========================================================
    # PAGE 10: SIX-MODEL QUALITATIVE COMPARISON
    # =========================================================
    p10 = doc.new_page(width=pw, height=ph)
    p10.insert_text(fitz.Point(mx, 45), "10. Architectural Qualitative Comparison across Six Models", fontsize=12, color=(0.11, 0.21, 0.36))
    p10.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig6_six_model_comparative.png'):
        p10.insert_image(fitz.Rect(mx, 55, pw - mx, 570), filename='full_doc_report/figures/fig6_six_model_comparative.png')
    p10.insert_text(fitz.Point(mx, 580), "Figure 9: Six-Model Comparative Qualitative Side-by-Side Gallery (ISIC, BUSI, KVASIR, KUB).", fontsize=8, color=(0.3, 0.3, 0.3))
    text_six = (
        "Comparative Architectural Observations:\n"
        "Columns: Native Image, U-Net, Attention U-Net, U-Net++, DeepLabV3+, MiT Transformer, GlobalMedFiLM baseline.\n"
        "Standard CNN models suffer severe boundary erosion on low-contrast modalities (KUB and BUSI). Heavy vision transformers (MiT) capture "
        "global context but generate checkerboard perimeter artifacts. GlobalMedFiLM achieves superior contour alignment via task-conditioned FiLM."
    )
    p10.insert_textbox(fitz.Rect(mx, 595, pw - mx, ph - 30), text_six, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p10, 10)

    # =========================================================
    # PAGE 11: EXTERNAL RETROSPECTIVE EVALUATION
    # =========================================================
    p11 = doc.new_page(width=pw, height=ph)
    p11.insert_text(fitz.Point(mx, 45), "11. External Retrospective Stress Testing (EXTERNAL884)", fontsize=12, color=(0.11, 0.21, 0.36))
    p11.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/F11_External_Quantitative_Evaluation_ReMedFiLM.png'):
        p11.insert_image(fitz.Rect(mx, 55, pw - mx, 290), filename='full_doc_report/figures/F11_External_Quantitative_Evaluation_ReMedFiLM.png')
    p11.insert_text(fitz.Point(mx, 298), "Figure 10: Retrospective External Stress Testing (Domain Shift Degradation vs Internal Validation Benchmark).", fontsize=8, color=(0.3, 0.3, 0.3))

    p11.insert_text(fitz.Point(mx, 315), "Table 4: Retrospective External Evaluation Evidence Summary (EXTERNAL884)", fontsize=9.5, color=(0.11, 0.21, 0.36))
    t4_y = 330
    t4_w = [110, 50, 40, 65, 65, 65, 145]
    t4_hdrs = ["External Cohort", "Analogue", "N", "Global Dice", "FULL Dice", "Δ (pp)", "Documented Transfer Vulnerability"]
    cur_x = mx
    for i, h in enumerate(t4_hdrs):
        p11.draw_rect(fitz.Rect(cur_x, t4_y, cur_x + t4_w[i], t4_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p11.insert_text(fitz.Point(cur_x + 3, t4_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t4_w[i]
        
    t4_rows = [
        ["CVC-ClinicDB", "KVASIR", "612", "0.6866", "0.6897", "+0.318", "Moderate shift (-13.4 pp vs VAL)"],
        ["BrEaST-Lesions-USG", "BUSI", "252", "0.7078", "0.7081", "+0.028", "Acoustic shift (-15.1 pp vs VAL)"],
        ["Stones (Stone-Positive)", "KUB", "6", "0.2695", "0.2738", "+0.429", "Severe radiographic transfer drop"],
        ["Stones (Stone-Free Neg.)", "KUB", "14", "0.0000", "0.0000", "0.000", "14 / 14 FALSE POSITIVE DETECTIONS"]
    ]
    for r_i, r_data in enumerate(t4_rows):
        row_y = t4_y + 18 + r_i * 16
        bg = (1.0, 0.92, 0.92) if r_i == 3 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p11.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t4_w[c_i], row_y + 16), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.7, 0.1, 0.1) if r_i == 3 else (0.1, 0.1, 0.1)
            p11.insert_text(fitz.Point(cur_x + 3, row_y + 11), v, fontsize=7, color=f_col)
            cur_x += t4_w[c_i]

    text_ext = (
        "Material Negative Finding — External False Positive Generation:\n"
        "In the external negative control cohort (Stones_where_are_you, n=14 stone-free radiographs), GlobalMedFiLM and BARR both produced "
        "false-positive calcification detections across all 14 images (mean Dice 0.0000). Post-safety gating rejected only 1 of 3 routed proposals, "
        "adopting 2 false-positive masks. This proves that while BARR mitigates boundary harm on positive lesions, it does NOT safeguard "
        "against false positive hallucination on completely stone-free imagery. This finding is disclosed prominently as a critical limitation."
    )
    p11.insert_textbox(fitz.Rect(mx, 420, pw - mx, ph - 30), text_ext, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p11, 11)

    # =========================================================
    # PAGE 12: EXTERNAL QUALITATIVE GALLERY
    # =========================================================
    p12 = doc.new_page(width=pw, height=ph)
    p12.insert_text(fitz.Point(mx, 45), "12. External Retrospective Qualitative Segmentation Cases", fontsize=12, color=(0.11, 0.21, 0.36))
    p12.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/F12_External_Qualitative_Composite_ReMedFiLM.png'):
        p12.insert_image(fitz.Rect(mx, 55, pw - mx, 570), filename='full_doc_report/figures/F12_External_Qualitative_Composite_ReMedFiLM.png')
    p12.insert_text(fitz.Point(mx, 580), "Figure 11: External Retrospective Cases (Beneficial, Harmful, Rejected, Non-Selected, and Stone-Free False-Positive).", fontsize=8, color=(0.3, 0.3, 0.3))
    text_ext_g = (
        "External Qualitative Analysis (Historic Retrospective Cohorts):\n"
        "  * Row 1: Accepted beneficial refinement in CVC-ClinicDB (CVC::160, Dice 0.806 -> 0.921, +11.5 pp).\n"
        "  * Row 2: Accepted harmful refinement in CVC-ClinicDB (CVC::135, Dice 0.182 -> 0.134, -4.78 pp; boundary over-dilation).\n"
        "  * Row 3: Safety-rejected refinement in CVC-ClinicDB (CVC::358, Safety probability 0.48 < 0.50; blocked, preserving global mask).\n"
        "  * Row 4: Representative non-selected case (CVC::551, Router determines refinement unnecessary, zero compute overhead).\n"
        "  * Row 5: Stone-free false positive failure in Stones_where_are_you (Bowel gas erroneously predicted as calculus; Dice 0.000)."
    )
    p12.insert_textbox(fitz.Rect(mx, 595, pw - mx, ph - 30), text_ext_g, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p12, 12)

    # =========================================================
    # PAGE 13: STAGE-WISE PROGRESSION & SANKEY FLOW
    # =========================================================
    p13 = doc.new_page(width=pw, height=ph)
    p13.insert_text(fitz.Point(mx, 45), "13. Model Progression & Stage-Wise Error Propagation", fontsize=12, color=(0.11, 0.21, 0.36))
    p13.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig_sankey_routing_safety.png'):
        p13.insert_image(fitz.Rect(mx, 55, pw - mx, 320), filename='full_doc_report/figures/fig_sankey_routing_safety.png')
    p13.insert_text(fitz.Point(mx, 328), "Figure 12: Stage-Wise Proposal Routing & Safety Acceptance Sankey Flow (ROUTER_DEVELOPMENT vs External).", fontsize=8, color=(0.3, 0.3, 0.3))

    text_sankey = (
        "Refinement Propagation Dynamics:\n"
        "  * In-Sample Flow (ROUTER_DEVELOPMENT, n=4,957): The benefit router selects 1,239 proposals (25.0% budget). The post-safety gate evaluates "
        "predictive safety, rejecting 34 proposals and adopting 1,205. Among adopted refinements, 815 cases are improved and 390 worsened (32.4% harm).\n"
        "  * External Flow (EXTERNAL884, n=884): Router selects 184 cases (20.8%). Safety gate blocks 45 proposals, adopting 139 (96 improved, 34 worsened, "
        "9 unchanged; 24.5% harm rate). Rejection successfully blocks 45 ambiguous proposals, preventing further negative transfer.\n"
        "  * Incremental Domain Progression Status: A thorough audit confirms that an incremental dataset growth experiment (adding ISIC, then BUSI, "
        "then KVASIR, then KUB sequentially to measure catastrophic forgetting) was NOT executed in the repository. It is recorded as "
        "INCREMENTAL_DATASET_PROGRESSION_NOT_EXECUTED rather than simulated from unrelated checkpoints."
    )
    p13.insert_textbox(fitz.Rect(mx, 345, pw - mx, ph - 30), text_sankey, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p13, 13)

    # =========================================================
    # PAGE 14: 13-ARM ABLATION MATRIX
    # =========================================================
    p14 = doc.new_page(width=pw, height=ph)
    p14.insert_text(fitz.Point(mx, 45), "14. Complete 13-Arm Component Ablation Study", fontsize=12, color=(0.11, 0.21, 0.36))
    p14.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/F15_Complete_13Arm_Ablation_ReMedFiLM.png'):
        p14.insert_image(fitz.Rect(mx, 55, pw - mx, 290), filename='full_doc_report/figures/F15_Complete_13Arm_Ablation_ReMedFiLM.png')
    p14.insert_text(fitz.Point(mx, 298), "Figure 15: ReMedFiLM 13-Arm Component Ablation and Safety Dynamics (Phase 28 Matrix): Routed Delta Dice and Harmful Activation Share.", fontsize=8, color=(0.3, 0.3, 0.3))

    p14.insert_text(fitz.Point(mx, 315), "Table 5: Primary Metrics across All 13 Ablation Arms (ROUTER_DEVELOPMENT4957)", fontsize=9.5, color=(0.11, 0.21, 0.36))
    t5_y = 330
    t5_w = [35, 175, 55, 50, 75, 60, 90]
    t5_hdrs = ["Arm", "Ablation Arm Configuration", "Routed N", "Budget", "Mean Routed Δ", "Improved", "Harmful Share"]
    cur_x = mx
    for i, h in enumerate(t5_hdrs):
        p14.draw_rect(fitz.Rect(cur_x, t5_y, cur_x + t5_w[i], t5_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p14.insert_text(fitz.Point(cur_x + 3, t5_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t5_w[i]
        
    t5_rows = [
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
    for r_i, r_data in enumerate(t5_rows):
        row_y = t5_y + 18 + r_i * 15
        bg = (0.85, 0.89, 0.93) if r_i == 8 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p14.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t5_w[c_i], row_y + 15), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.11, 0.21, 0.36) if r_i == 8 else (0.1, 0.1, 0.1)
            p14.insert_text(fitz.Point(cur_x + 3, row_y + 10), v, fontsize=6.5, color=f_col)
            cur_x += t5_w[c_i]

    text_abl = (
        "Ablation Insights & Statistical Caveat:\n"
        "  * Necessity of Global Conditioning: Arm F1 (removing p_global from refiner input) causes catastrophic collapse (-3.26 pp delta, 68.8% harm).\n"
        "  * Role of Routing vs Post-Safety: Benefit routing reduces harmful activations from 42.7% (A1) to 33.3% (A7). Safety gating (A8) further "
        "eliminates 34 harmful proposals, elevating routed delta to +0.75 pp. However, the contrast A8 vs A7 95% CI spans zero; this increment is "
        "descriptive and does not establish a statistically proven positive mean Dice effect."
    )
    p14.insert_textbox(fitz.Rect(mx, 550, pw - mx, ph - 30), text_abl, fontsize=8, color=(0.15, 0.15, 0.15), lineheight=1.2)
    decorate(p14, 14)

    # =========================================================
    # PAGE 15: REPRODUCIBILITY (3 SEEDS) & INTERPRETABILITY
    # =========================================================
    p15 = doc.new_page(width=pw, height=ph)
    p15.insert_text(fitz.Point(mx, 45), "15. Statistical Reproducibility & Router Interpretability", fontsize=12, color=(0.11, 0.21, 0.36))
    p15.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/F17_Seed_Reproducibility_ReMedFiLM.png'):
        p15.insert_image(fitz.Rect(mx, 55, pw - mx, 280), filename='full_doc_report/figures/F17_Seed_Reproducibility_ReMedFiLM.png')
    p15.insert_text(fitz.Point(mx, 288), "Figure 14: Three-Seed Refinement Distribution (Seeds 42, 123, 3407) across Shared Global Backbone.", fontsize=8, color=(0.3, 0.3, 0.3))

    p15.insert_text(fitz.Point(mx, 305), "Table 6: Three-Seed Validation Performance Summary on VAL808", fontsize=9.5, color=(0.11, 0.21, 0.36))
    t6_y = 320
    t6_w = [75, 75, 75, 75, 75, 75, 90]
    t6_hdrs = ["Seed", "Global Dice", "BARR Dice", "Net Shift (Δ pp)", "Routed Count", "Adopted Count", "Harmful Count"]
    cur_x = mx
    for i, h in enumerate(t6_hdrs):
        p15.draw_rect(fitz.Rect(cur_x, t6_y, cur_x + t6_w[i], t6_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p15.insert_text(fitz.Point(cur_x + 3, t6_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t6_w[i]
        
    t6_rows = [
        ["Seed 42", "0.835079", "0.837862", "+0.2783", "183", "165", "31"],
        ["Seed 123", "0.835079", "0.837910", "+0.2831", "185", "168", "29"],
        ["Seed 3407", "0.835079", "0.837815", "+0.2736", "181", "163", "33"],
        ["Mean ± SD", "0.835079 ± 0.000", "0.837862 ± 0.00004", "+0.2783 ± 0.004", "183 ± 2", "165 ± 2", "31 ± 2"]
    ]
    for r_i, r_data in enumerate(t6_rows):
        row_y = t6_y + 18 + r_i * 16
        bg = (0.85, 0.89, 0.93) if r_i == 3 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p15.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t6_w[c_i], row_y + 16), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.11, 0.21, 0.36) if r_i == 3 else (0.1, 0.1, 0.1)
            p15.insert_text(fitz.Point(cur_x + 3, row_y + 11), v, fontsize=7, color=f_col)
            cur_x += t6_w[c_i]

    text_rep = (
        "Reproducibility Disclosure & Router Attribution:\n"
        "  * Shared Backbone Disclosure: Crucially, Seeds 42, 123, and 3407 share an identical pre-trained GlobalMedFiLM backbone. The tight standard "
        "deviation (0.837862 ± 0.00004) measures the initialization stability of R_psi and B_phi, not independent end-to-end training replicates.\n"
        "  * Router Feature Attribution (Phase 35): Integrated Gradients on B_phi demonstrate that router decisions are strongly driven by boundary "
        "entropy (42.1% attribution) and foreground area (31.4% attribution), with modest task-embedding steering (26.5%)."
    )
    p15.insert_textbox(fitz.Rect(mx, 410, pw - mx, ph - 30), text_rep, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p15, 15)

    # =========================================================
    # PAGE 16: PERTURBATION ROBUSTNESS & FAILURE TAXONOMY
    # =========================================================
    p16 = doc.new_page(width=pw, height=ph)
    p16.insert_text(fitz.Point(mx, 45), "16. Perturbation Robustness & Comprehensive Failure Taxonomy", fontsize=12, color=(0.11, 0.21, 0.36))
    p16.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/F18_Robustness_Perturbation_ReMedFiLM.png'):
        p16.insert_image(fitz.Rect(mx, 55, pw - mx, 300), filename='full_doc_report/figures/F18_Robustness_Perturbation_ReMedFiLM.png')
    p16.insert_text(fitz.Point(mx, 308), "Figure 15: Robustness Degradation across Image Perturbations and Complete Failure Mode Taxonomy.", fontsize=8, color=(0.3, 0.3, 0.3))

    p16.insert_text(fitz.Point(mx, 325), "Table 7: Systematic Perturbation Degradation Matrix (Mean Paired Δ Dice pp)", fontsize=9.5, color=(0.11, 0.21, 0.36))
    t7_y = 340
    t7_w = [140, 100, 100, 100, 100]
    t7_hdrs = ["Perturbation Condition", "BUSI (US)", "ISIC (Derm.)", "KVASIR (Endo.)", "KUB (X-ray)"]
    cur_x = mx
    for i, h in enumerate(t7_hdrs):
        p16.draw_rect(fitz.Rect(cur_x, t7_y, cur_x + t7_w[i], t7_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p16.insert_text(fitz.Point(cur_x + 3, t7_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t7_w[i]
        
    t7_rows = [
        ["Gaussian Noise (High)", "-8.99 pp", "-3.15 pp", "-6.04 pp", "-36.36 pp (Catastrophic)"],
        ["Gaussian Blur (High)", "-0.31 pp", "-0.50 pp", "-1.44 pp", "-5.63 pp"],
        ["Resolution Subsampling (0.50x)", "-0.37 pp", "-0.46 pp", "-1.66 pp", "-5.44 pp"],
        ["Low Gamma Attenuation", "-1.27 pp", "-0.25 pp", "-0.94 pp", "-0.43 pp"],
        ["Low Contrast Scaling", "-0.24 pp", "-0.53 pp", "-0.05 pp", "-0.48 pp"],
        ["Negative Brightness Shift", "-0.60 pp", "-0.09 pp", "-0.79 pp", "-1.67 pp"]
    ]
    for r_i, r_data in enumerate(t7_rows):
        row_y = t7_y + 18 + r_i * 15
        bg = (1.0, 0.92, 0.92) if r_i == 0 else ((0.97, 0.98, 0.99) if r_i % 2 == 1 else (1, 1, 1))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p16.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t7_w[c_i], row_y + 15), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.7, 0.1, 0.1) if (r_i == 0 and c_i == 4) else (0.1, 0.1, 0.1)
            p16.insert_text(fitz.Point(cur_x + 3, row_y + 10), v, fontsize=7, color=f_col)
            cur_x += t7_w[c_i]

    text_rob = (
        "Radiographic Fragility under Noise:\n"
        "Abdominal radiography is profoundly vulnerable to high Gaussian noise (-36.36 pp degradation). Plain radiographs rely on subtle radio-opacity "
        "differences between bone cortex and calculus. Noise corrupts low-contrast calyx edges, causing false positive stone proposals across ribs."
    )
    p16.insert_textbox(fitz.Rect(mx, 455, pw - mx, ph - 30), text_rob, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p16, 16)

    # =========================================================
    # PAGE 17: COMPUTATIONAL EFFICIENCY & PARETO TRADEOFFS
    # =========================================================
    p17 = doc.new_page(width=pw, height=ph)
    p17.insert_text(fitz.Point(mx, 45), "17. Computational Complexity & Accuracy-Cost Trade-Offs", fontsize=12, color=(0.11, 0.21, 0.36))
    p17.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)
    if os.path.exists('full_doc_report/figures/fig_accuracy_vs_cost_detail.png'):
        p17.insert_image(fitz.Rect(mx, 55, pw - mx, 340), filename='full_doc_report/figures/fig_accuracy_vs_cost_detail.png')
    p17.insert_text(fitz.Point(mx, 348), "Figure 16: Accuracy vs Computational Complexity Pareto Trade-Off Frontier (Macro Dice vs GMACs and Latency).", fontsize=8, color=(0.3, 0.3, 0.3))

    text_cost = (
        "Complexity Analysis & Hardware Profiling (NVIDIA RTX 3060 Ti, Batch Size 1):\n"
        "  * Parameter Footprint: GlobalMedFiLM = 3,523,001 params; Refiner R_psi = 1,276,401 params; Router B_phi = 36,801 params; Post-Safety "
        "S_omega = 1,217 params; Total Inference Bundle = 4,837,420 parameters (4.84M). This is substantially lighter than DeepLabV3+ (40.35M) "
        "and MiT Transformer U-Net (16.35M).\n"
        "  * Analytical MACs: Global-only inference requires 31.55 GMACs. Under Arm A8 budget (routing 24.3% of candidates), expected conditional "
        "execution complexity is 32.44 GMACs—a 67.2% reduction compared to Transformer MiT U-Net (99.10 GMACs).\n"
        "  * Real Latency: Forward-only backbone latency averages 15.77 ms. The full conditional pipeline averages 15.72 ms on skipped paths and "
        "18.89 ms on executed refinement paths, confirming that selective routing minimizes latency overhead."
    )
    p17.insert_textbox(fitz.Rect(mx, 365, pw - mx, ph - 30), text_cost, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p17, 17)

    # =========================================================
    # PAGE 18: HISTORICAL TEST1683 BENCHMARK DISCLOSURE
    # =========================================================
    p18 = doc.new_page(width=pw, height=ph)
    p18.insert_text(fitz.Point(mx, 45), "18. Historical Prospective TEST1683 Evaluation Disclosure", fontsize=12, color=(0.11, 0.21, 0.36))
    p18.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)

    text_test = (
        "Audit Disclosure of Prior TEST Exposure:\n"
        "In Phase 39 (revision v1.2), the canonical prospective test partition (n=1,683) was evaluated following two earlier disclosed technical "
        "aborts (exit code 1 on process launch). The historical one-shot scientific results recorded in phase39_final_test_v1_2_scientific_result.json "
        "are documented below:\n\n"
        "Historical TEST1683 Descriptive Outcome (Phase 39 v1.2):\n"
        "  * ISIC 2018 (n = 735): Mean Dice = 0.8869 (Median = 0.9349)\n"
        "  * BUSI-WHU (n = 174): Mean Dice = 0.8504 (Median = 0.8899)\n"
        "  * Kvasir-SEG (n = 216): Mean Dice = 0.8507 (Median = 0.9096)\n"
        "  * KUB-StoneX (n = 558): Mean Dice = 0.7377 (Median = 0.8421)\n"
        "  * Overall Macro Dice = 0.831437 across 1,683 test cases.\n\n"
        "Governance & Anti-Leakage Attestation:\n"
        "In strict compliance with research software governance, the present V5 report did NOT open, re-evaluate, or alter TEST1683 artifacts. "
        "The historical result is disclosed solely for transparency. No comparative superiority claims over competing models are asserted on TEST1683 "
        "because external baselines were not evaluated under identical prospective protocols."
    )
    p18.insert_textbox(fitz.Rect(mx, 60, pw - mx, 350), text_test, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.25)
    decorate(p18, 18)

    # =========================================================
    # PAGE 19: SUPPORTED FINDINGS VS MISSING EVIDENCE
    # =========================================================
    p19 = doc.new_page(width=pw, height=ph)
    p19.insert_text(fitz.Point(mx, 45), "19. Supported Scientific Claims vs. Critical Evidence Gaps", fontsize=12, color=(0.11, 0.21, 0.36))
    p19.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)

    p19.insert_text(fitz.Point(mx, 58), "Table 8: Scientific Status Matrix — Experimentally Supported Findings vs Unresolved Frontiers", fontsize=9.5, color=(0.11, 0.21, 0.36))
    t8_y = 75
    t8_w = [110, 80, 350]
    t8_hdrs = ["Evidence Category", "Status", "Scientific Finding / Documented Evidence Gap"]
    cur_x = mx
    for i, h in enumerate(t8_hdrs):
        p19.draw_rect(fitz.Rect(cur_x, t8_y, cur_x + t8_w[i], t8_y + 18), color=(0.11, 0.21, 0.36), fill=(0.11, 0.21, 0.36))
        p19.insert_text(fitz.Point(cur_x + 3, t8_y + 12), h, fontsize=7.5, color=(1, 1, 1))
        cur_x += t8_w[i]
        
    t8_rows = [
        ["Internal Multi-Domain Gain", "SUPPORTED", "GlobalMedFiLM achieves 0.8351 macro Dice; FULL BARR achieves 0.8379 (+0.28 pp overall gain on VAL808)."],
        ["Risk-Averse Routing Dynamics", "SUPPORTED", "Learned routing cuts harmful activations from 42.7% (A1) to 32.4% (A8), raising routed delta to +0.75 pp."],
        ["Anatomical Subgroup Refinements", "SUPPORTED", "Verified gains on Bladder Stones (+1.46 pp) and Ureteric Stones (+1.06 pp) in plain radiography."],
        ["External Domain Shift Fragility", "MATERIAL FAILURE", "Material failure on stone-free radiographs (14/14 false positive detections; Dice 0.000)."],
        ["C1 Causal FiLM Attribution Study", "MISSING EVIDENCE", "0 of 6 planned genuine paired C1 training runs executed; causal FiLM attribution remains unproven."],
        ["C2 Causal Component Attribution", "MISSING EVIDENCE", "Component ablations conducted in-sample on ROUTER_DEVELOPMENT; causal held-out validation pending."],
        ["C3 24-Cell Baseline Comparison", "MISSING EVIDENCE", "0 of 24 genuine matched multi-seed baseline cells completed; comparative claims limited to Phase 21."],
        ["Incremental Domain Progression", "MISSING EVIDENCE", "Incremental dataset training was not executed in repository (INCREMENTAL_DATASET_PROGRESSION_NOT_EXECUTED)."]
    ]
    for r_i, r_data in enumerate(t8_rows):
        row_y = t8_y + 18 + r_i * 24
        bg = (1.0, 0.92, 0.92) if "FAILURE" in r_data[1] else ((0.95, 0.95, 0.95) if "MISSING" in r_data[1] else (0.92, 0.98, 0.92))
        cur_x = mx
        for c_i, v in enumerate(r_data):
            p19.draw_rect(fitz.Rect(cur_x, row_y, cur_x + t8_w[c_i], row_y + 24), color=(0.85, 0.85, 0.85), fill=bg)
            f_col = (0.7, 0.1, 0.1) if "FAILURE" in r_data[1] else ((0.4, 0.4, 0.4) if "MISSING" in r_data[1] else (0.1, 0.4, 0.1))
            if c_i == 1:
                p19.insert_text(fitz.Point(cur_x + 5, row_y + 15), v, fontsize=7, color=f_col)
            elif c_i == 0:
                p19.insert_text(fitz.Point(cur_x + 3, row_y + 15), v, fontsize=7, color=(0.11, 0.21, 0.36))
            else:
                p19.insert_textbox(fitz.Rect(cur_x + 3, row_y + 2, cur_x + t8_w[c_i] - 3, row_y + 22), v, fontsize=7, color=(0.1, 0.1, 0.1), lineheight=1.1)
            cur_x += t8_w[c_i]

    decorate(p19, 19)

    # =========================================================
    # PAGE 20: CONCLUSION & PAPER-WRITING RECOMMENDATIONS
    # =========================================================
    p20 = doc.new_page(width=pw, height=ph)
    p20.insert_text(fitz.Point(mx, 45), "20. Conclusions & Peer-Reviewed Submission Recommendations", fontsize=12, color=(0.11, 0.21, 0.36))
    p20.draw_line(fitz.Point(mx, 49), fitz.Point(pw - mx, 49), color=(0.11, 0.21, 0.36), width=1)

    text_conc = (
        "Summary of Empirical Standing:\n"
        "ReMedFiLM (FULL RA-MedFiLM-BARR) demonstrates that pairing global task-conditioned FiLM modulation with selective, risk-averse residual refinement "
        "achieves competitive multi-domain segmentation performance (0.8379 macro Dice) at a fraction of the computational footprint of vision "
        "transformers (32.44 GMACs vs 99.10 GMACs).\n\n"
        "Guidance for IEEE TMI / Medical Image Analysis Submission:\n"
        "  1. Center the Narrative on Risk-Averse Routing: The strongest methodological contribution is demonstrating that unconstrained secondary "
        "refinement is unsafe (42.7% harm rate in Arm A1), and that learned routing paired with safety gating successfully controls degradation.\n"
        "  2. Disclose External Fragility Transparently: Reviewers will respect transparent reporting of the 14/14 false-positive detection rate on "
        "stone-free radiographs. Position this as an open radiological challenge requiring dedicated negative-case calibration losses.\n"
        "  3. Avoid Overstated Causal Claims: Clarify that while GlobalMedFiLM achieves strong empirical results, the formal paired C1 causal "
        "attribution study and 24-cell matched baseline matrix remain prospective goals.\n\n"
        "Final Verification & Provenance Sign-Off:\n"
        "This V5 report, companion figures, and supporting CSV indices provide an unbroken cryptographic audit trail across all 808 validation "
        "and 884 retrospective external cases. The research software is technically prepared, reproducible, and ready for publication authoring."
    )
    p20.insert_textbox(fitz.Rect(mx, 60, pw - mx, ph - 30), text_conc, fontsize=8.5, color=(0.15, 0.15, 0.15), lineheight=1.3)
    decorate(p20, 20)

    # Save with compression (deflate + garbage collection)
    doc.save(pdf_out, deflate=True, garbage=4, clean=True)
    doc.close()
    print(f"Successfully generated 20-page master PDF: {pdf_out} ({os.path.getsize(pdf_out)/(1024*1024):.2f} MB)")

build_v5_pdf()
