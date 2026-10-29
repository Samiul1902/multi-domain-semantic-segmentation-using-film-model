# R1 synthetic validation and reproducibility

**SYNTHETIC_TEST_ONLY. Scientific execution unchanged, not authorized.** No real training, inference, GT scoring, checkpoint loading/modification, BARR-M1 execution, TEST/ROUTER_HOLDOUT record access, protocol/release edit or manuscript edit. Ontology used permitted source/protocol and historical aggregate development records plus TRAIN/VAL metadata inspection, not image/mask pixels. No actual patient/sample records are reproduced here.

## Findings

1. **Binary semantics preserved.** Four foreground tasks, not four anatomical classes. KUB intensities 1/2/3 are not subclasses; Kidney/Bladder/Ureteric labels are subgroup metadata. Kvasir RGB JPEG masks include low/high nonzero intensities; frozen `>0`, first-channel reduction is retained, not retrospectively corrected. Annotation provenance and physical spacing are unavailable in inspected records.
2. **C1 estimand preserved mathematically.** Matched per-image differences; within-domain means; four domains equally weighted; three fixed seeds equally weighted. Compatibility `>=0.5`, epsilon `1e-7`, float32 counts. Frozen protocol and selected `best_records` authority unchanged. Generic new conventions do not substitute for historical outputs.
3. **C1 uncertainty conditional.** 10,000 PCG64 draws, seed 20261027, paired domain-stratified patient/case sampling, shared draws across seeds, percentile 95% interval. KUB IDs mandatory; non-KUB cases. Seed SD/range descriptive, no seed-population inference. Development selection is not independent generalization or clinical benefit.
4. **BUSI discrepancy disclosed.** Phase-19 records a leakage-group sidecar although canonical patient/case fields are unavailable. Its eligibility was not independently verified; frozen C1 image resampling is unchanged. Future non-C1 protocols may prospectively audit grouping, not invent IDs or retrofit C1.
5. **Geometry explicit.** Euclidean distances between equally weighted 8-connected boundary pixel centres with row/column spacing. Not continuous contours or length-weighted surfel Dice. Unknown spacing means pixels, never mm. Empty surfaces undefined and counted, not zero error.
6. **Missingness explicit.** Zero-denominator ratios null; both-empty Dice/IoU=1, one-empty overlap=0. Missing patient/source/subgroup estimates NOT_AVAILABLE, not fabricated patients. Descriptive complete pairs disclose missingness; primary bootstrap refuses missing/duplicate/nonfinite pairs. C1 checks six run statuses and declared roster; independent provenance audit still required.
7. **Integrity not approval.** Immutable snapshots/hashes detect drift and declared prohibited references. No loader. Callers can lie about provenance; utilities cannot manufacture scientific approval. Generic C2/C3 utilities are not approved protocols.

## Mathematical tests and tolerances

| Functions | Reference | Assumptions / tolerance |
|---|---|---|
| binary metrics | hand counts + sklearn confusion matrix | discrete masks; counts exact; fractions relative 1e-6 / absolute 1e-12 |
| multiclass | 4-pixel confusion, micro .75 Dice / .6 IoU | exclusive declared labels, reference-support weights; relative 1e-6 |
| C1 compatibility | frozen Phase21 helper, artificial logits/ties | float32; exact compared values; no model forward |
| surfaces | single-pixel/touching analytical cases; independent boundary enumeration + brute-force cdist | border/disconnected/anisotropic geometry; absolute 1e-12 / relative 0 for reference |
| aggregation | analytical macro and unequal image counts | image mean != pooled pixels; missing IDs unavailable |
| bootstrap | seed cancellation + unequal-cluster manual draws | patient multiplicity, shared seed draws; absolute 1e-12 |
| statistics | paired mean and Holm/BH/Bonferroni examples | sample SD ddof=1; no n=1 inference |
| contract/output | corrupt shapes/IDs/schema/checkpoints/probabilities, duplicate/NaN/Inf, protected references, immutable copies and deterministic bytes | hashes exact; synthetic arrays only; refuse differing overwrite |

Final executed counts/node names are in `D:\Softfors\jup\docs\evaluation_r1\synthetic_test_report.json`. The initial reporting-harness hook naming error occurred before test collection and was corrected; no scientific execution occurred. Passing tests establish tested mathematics/software behavior, not coverage guarantees, annotation quality or real-data performance.

## Reproduction

Package: `D:\Softfors\jup\src\research\evaluation_r1\`.
Test command: `D:\Softfors\jup\docs\evaluation_r1\README.md`.
Examples: `D:\Softfors\jup\.venv\Scripts\python.exe -m src.research.evaluation_r1.synthetic --output D:\Softfors\jup\docs\evaluation_r1\examples`.
All JSON/CSV examples are SYNTHETIC_TEST_ONLY. Scalar comparison uses 200 generic demonstration draws, **not** C1 evidence. C1 wrapper separately tested at frozen 10,000 draws. Do not put synthetic results in measured-performance manuscript tables.

`artifact_manifest.json` lists task-owned hashes, permitted source identities and frozen preservation, excluding its own impossible self-hash. Git SHA reported outside its own commit. Pre-existing work excluded. No remote configured; no invented remote.
