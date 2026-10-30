PHASE 13B — LEARNED HIGH-RECALL KUB LOCALIZER

PURPOSE
Phase 13 simple proposals passed scientifically but Phase-14 gate was WEAK:
- overall recall90 = 0.743590
- Tiny recall90 = 0.684932
- 0/16 globally missed Tiny components recovered
- 0/7 global-empty FULL_FIELD cases recovered
- multi-component recall90 = 0.70

Goal:
Train a dedicated GT-free-at-inference learned localizer that predicts
objectness/center heatmaps and test whether it recovers these hard cases.

DATA
TRAIN: KUB FULL_FIELD only, expected 771 images.
VAL: KUB FULL_FIELD only, expected 106 images / 156 components.
Frozen VAL strata:
Tiny 73, Small 29, Medium 36, Large 18.
TEST and external data remain locked.

MODEL
Implement one compact U-Net-style localization network:
src/models/kub_localizer.py

Input: grayscale FULL_FIELD image.
Output: one-channel objectness heatmap.
Random initialization.
No pretrained weights.

SUPERVISION
Generate TRAIN-only soft center heatmaps from GT component centroids.

Predeclared sigma candidates:
3, 5, 7 pixels.

Resolution candidates:
512, 768.

Maximum candidates:
6.

Do not expand this grid.

LOSS
Freeze before training:
0.75 focal loss + 0.25 soft Dice
Focal gamma=2, alpha=0.25.

TRAINING
seed=42
AdamW
lr=1e-4
weight_decay=1e-4
CosineAnnealingLR
AMP CUDA
max_epochs=100
early_stopping=15
effective_batch=4

Physical batch fallback:
4
then 2 + accumulation2
then 1 + accumulation4.

If CUDA unavailable:
CHECK_REQUIRED and stop.

PROPOSAL POSTPROCESSING
VAL-only compact grid:

threshold:
0.10, 0.20, 0.30, 0.40, 0.50

margin:
0.10, 0.20

Top-K:
3, 5

NMS IoU:
0.30

Proposal-generation API must accept NO GT.

GT may only be used after proposals are generated for evaluation.

PRIMARY HIT
A GT component is localized if one predicted ROI contains >=90% of its
original-space pixels.

Also report:
>=50%
any-overlap
continuous coverage.

FROZEN HARD SETS
Use exactly the Phase-13 frozen:
- 16 globally missed Tiny components
- 7 global-empty FULL_FIELD images

Do not redefine these sets.

MODEL SELECTION
Lexicographic:

1. maximize recovered frozen 16 Tiny misses at >=90%
2. maximize recovered frozen 7 global-empty cases at >=90%
3. maximize overall Tiny recall90
4. maximize overall component recall90
5. maximize multi-component recall90
6. minimize ROI area fraction
7. minimize proposals/image
8. prefer 512 if still tied

Do not select by segmentation Dice.

PHASE-14 GATE = YES only if ALL:

A. >=8/16 hard Tiny recovered90
B. >=4/7 global-empty recovered90
C. overall Tiny recall90 >=0.85
D. overall component recall90 >=0.85
E. mean ROI area fraction <=0.10
F. mean proposals/image <=5

Otherwise:
WEAK or NO.

REQUIRED OUTPUTS
Reusable:
src/models/kub_localizer.py
src/inference/learned_roi.py

Experiments:
phase13b_kub_localizer_r512_s3_seed42
phase13b_kub_localizer_r512_s5_seed42
phase13b_kub_localizer_r512_s7_seed42
phase13b_kub_localizer_r768_s3_seed42
phase13b_kub_localizer_r768_s5_seed42
phase13b_kub_localizer_r768_s7_seed42

Save best.pt/latest.pt with complete resume state.

Tables:
phase13b_localizer_candidate_summary.csv
phase13b_localizer_search.csv
phase13b_localizer_per_component.csv
phase13b_localizer_per_image.csv
phase13b_localizer_size_summary.csv
phase13b_localizer_hard_case_recovery.csv
phase13b_localizer_multicomponent.csv
phase13b_simple_vs_learned_localizer.csv

Figures:
training curves
simple-vs-learned recall
Tiny miss recovery
global-empty recovery
size localization
recall-vs-ROI-area
multi-component localization
heatmap examples

Notebook:
notebooks/11b_kub_learned_localizer.ipynb

Notebook is display/reporting only and must not retrain during Run All.

Audit:
reports/audits/phase13b_learned_localizer.json
reports/audits/phase13b_learned_localizer.md

TESTS
Add tests for:
heatmap target generation
centroid mapping
multi-component targets
network forward/backward
checkpoint roundtrip
proposal extraction
coordinate mapping
GT-free inference API
TEST guard
resume state

Run:
python -m pytest
python -m compileall -q src scripts tests

GOVERNANCE
TEST reads = 0
No TEST metrics
No external data
Experiment A untouched
No regional refiner training
No Phase 14

STOP after Phase 13B.