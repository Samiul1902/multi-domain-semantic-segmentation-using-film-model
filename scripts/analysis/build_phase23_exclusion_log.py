import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TAB = ROOT / "reports" / "tables"

COLS = ["title", "year", "reason_screened", "reason_excluded"]

rows = [
 # --- excluded: not segmentation ---
 {"title": "Adaptive Computation Time for Recurrent Neural Networks (ACT)", "year": 2016,
  "reason_screened": "learned halting / conditional computation; cost penalty",
  "reason_excluded": "NOT a segmentation method; retained only as general-CV precedence context, excluded from the segmentation-relevant detail comparison"},
 {"title": "Mixture-of-Depths: Dynamically Allocating Compute in Transformer-Based Language Models", "year": 2024,
  "reason_screened": "per-token compute routing; resource-aware",
  "reason_excluded": "language modelling, not segmentation; no quality-benefit target"},

 # --- excluded: only uncertainty, no action benefit ---
 {"title": "UHR-Net: Uncertainty-Aware Hypergraph Refinement Network for Medical Lesion Segmentation", "year": 2026,
  "reason_screened": "uncertainty-guided refinement in medical segmentation",
  "reason_excluded": "ONLY CURRENT UNCERTAINTY — refinement is applied unconditionally where uncertainty is high; no prediction of the BENEFIT of the refinement, no execute/skip gate"},
 {"title": "Uncertainty-Guided Incremental Gaussian Processes (Biomedical Signal Processing & Control)", "year": 2026,
  "reason_screened": "uncertainty-guides-refinement family",
  "reason_excluded": "ONLY CURRENT UNCERTAINTY; no paired gain target, no action gating, no cost"},
 {"title": "DEviS: Toward Reliable Medical Image Segmentation by Modeling Predictive Uncertainty", "year": 2025,
  "reason_screened": "predictive-uncertainty modelling for medical segmentation",
  "reason_excluded": "ONLY UNCERTAINTY/CALIBRATION; supplies an uncertainty signal but no benefit-of-action prediction and no gate"},

 # --- excluded: predicts quality but not action benefit ---
 {"title": "Real-time Prediction of Segmentation Quality", "year": 2018,
  "reason_screened": "direct quality prediction for segmentation",
  "reason_excluded": "PREDICTS CURRENT QUALITY, not refined-minus-global gain; no action, no cost (retained separately as a low-detail MEDIUM-risk contextual row, excluded from the deep comparison)"},
 {"title": "Uncertainty-Aware Segmentation Quality Prediction (arXiv:2508.01460)", "year": 2025,
  "reason_screened": "GT-free segmentation quality prediction",
  "reason_excluded": "PREDICTS CURRENT QUALITY; no future action, no paired gain, no routing"},
 {"title": "Coherence-Based Segmentation Quality Evaluator", "year": 2026,
  "reason_screened": "GT-free quality evaluation",
  "reason_excluded": "PREDICTS CURRENT QUALITY; no action benefit, no gate"},

 # --- excluded: post-refinement selection only ---
 {"title": "SegRefiner: Towards Model-Agnostic Segmentation Refinement with Discrete Diffusion Process", "year": 2023,
  "reason_screened": "model-agnostic refinement primitive",
  "reason_excluded": "POST-REFINEMENT-ONLY / no selection at all — it always refines; it is the expensive step our gate would decide on, not a competing gate"},

 # --- excluded: no paired gain target ---
 {"title": "Balancing Accuracy and Efficiency in Budget-Aware Early-Exit Neural Networks (EENN)", "year": 2024,
  "reason_screened": "budget-aware early exit",
  "reason_excluded": "NO PAIRED GAIN TARGET — exits on a confidence/difficulty threshold; not trained on Q(refined)-Q(global); classification-oriented"},
 {"title": "Soft Dice Confidence (plug-in variant, deferred appendix ablations)", "year": 2024,
  "reason_screened": "GT-free confidence with abstention",
  "reason_excluded": "NO EXECUTE/SKIP MECHANISM for an expensive action; abstention only"},

 # --- excluded: unrelated resource routing ---
 {"title": "Dynamic resolution networks / spatially adaptive computation (general family)", "year": 2020,
  "reason_screened": "adaptive computation at the input-resolution level",
  "reason_excluded": "UNRELATED RESOURCE ROUTING — changes resolution/depth of a single network; no optional external refinement, no paired gain, no fallback"},
 {"title": "MoE with Expert Choice Routing", "year": 2022,
  "reason_screened": "cost-aware routing in MoE",
  "reason_excluded": "UNRELATED ROUTING TARGET — token-to-expert assignment; no quality-gain target, no segmentation refinement"},

 # --- excluded: UNVERIFIABLE ---
 {"title": "On the Role of Computation in Reinforcement Learning (OpenReview 3Hge4SAjEN)", "year": None,
  "reason_screened": "value-of-computation in RL",
  "reason_excluded": "UNVERIFIED — author/venue could not be confirmed against the primary record this session; excluded from the authoritative matrix"},
 {"title": "When Does Learning to Stop Help? A Cost-Aware Study of Early Stopping for Reasoning Models (arXiv:2606.30852)", "year": 2026,
  "reason_screened": "cost-aware learned stopping",
  "reason_excluded": "UNVERIFIED — only aggregator metadata available; excluded from the authoritative matrix"},
 {"title": "HyDRA: Hybrid Dynamic Routing (arXiv:2605.17106)", "year": 2026,
  "reason_screened": "cost-aware dynamic routing",
  "reason_excluded": "UNVERIFIED — aggregator metadata only; excluded (also LLM-domain, not CV)"},
 {"title": "ROI-Reasoning (arXiv:2601.03822)", "year": 2026,
  "reason_screened": "pre-computation benefit estimation",
  "reason_excluded": "UNVERIFIED — aggregator metadata only; excluded from the authoritative matrix"},
 {"title": "A cloud-edge adaptive lightweight network with dynamic offloading (Scientific Reports 2026)", "year": 2026,
  "reason_screened": "device/edge-cost-aware medical segmentation",
  "reason_excluded": "UNVERIFIED — publisher redirect blocked full confirmation; potential relevance to device-cost routing flagged for a future verified pass"},
 {"title": "EA-LiteUNet (arXiv:2608.15537)", "year": 2026,
  "reason_screened": "edge-adaptive lightweight segmentation",
  "reason_excluded": "UNVERIFIED — title from search metadata only; mechanism unconfirmed"},
 {"title": "Edge-SegStar (Biomedical Signal Processing & Control)", "year": 2026,
  "reason_screened": "resource-efficient boundary-sensitive segmentation",
  "reason_excluded": "UNVERIFIED — title from search metadata only; mechanism unconfirmed"},
 {"title": "MICCAI 'Dynamic Routing paper' (secondary citation)", "year": None,
  "reason_screened": "dynamic routing in medical segmentation",
  "reason_excluded": "UNVERIFIED — surfaced only as a secondary reference; could not be resolved to a distinct primary record"},
 {"title": "US 12,685,594 (USPTO Gazette week 29, 2026)", "year": 2026,
  "reason_screened": "patent scan",
  "reason_excluded": "UNVERIFIED RELEVANCE — title not captured; no patentability conclusion drawn"},
]

with open(TAB / "phase23_excluded_nearby_works.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"excluded rows: {len(rows)}")
unv = sum(1 for r in rows if r["reason_excluded"].startswith("UNVERIFIED"))
print(f"unverified excluded: {unv}")
print("written:", TAB / "phase23_excluded_nearby_works.csv")
