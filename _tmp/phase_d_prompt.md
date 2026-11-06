<system-reminder data-role="user-context">
<craft_mode>
You are now in Agent mode. Continue with the task in the new mode, you can edit files freely. File writing and editing capabilities are now enabled, allowing you to create, modify, and save files directly to complete the task.
</craft_mode>
</system-reminder>
<system-reminder data-role="additional-data">
<current_time>
Tuesday, November 3, 2026 at 16:38:52 GMT+6
</current_time>
</system-reminder>
<user_query># RA-MedFiLM-BARR — PHASE D: GPU PERFORMANCE, RELIABILITY & REPRODUCIBILITY

Repository: D:\Softfors\jup
Agent: Google Antigravity

## ROLE AND OBJECTIVE

Act as a senior PyTorch performance engineer, scientific reproducibility specialist and independent research software auditor.

Complete Phase D of the RA-MedFiLM-BARR research implementation.

The system already contains:

- Phase A: FULL three-seed training pipeline
- Phase B: Lite three-seed training pipeline
- Phase C: Unified eight-model evaluation infrastructure
- Synthetic 24-cell comparison matrix
- Canonical GlobalMedFiLM and five external baselines
- Checkpoint provenance and recovery mechanisms

Your task is to make the existing implementation reliable, efficient and reproducible on the available workstation.

**Prioritize fixing real engineering defects, not creating additional governance processes or research frameworks.**

Complete the whole assignment, test it, commit task-owned verified changes and STOP.

Do not run genuine research training, protected evaluation or institutional authorization operations.

---

## 1. Verify the starting state

Inspect:

- Git HEAD and working-tree modifications
- FULL training pipeline
- Lite training pipeline
- Stage 6 evaluation matrix
- Phase C evaluation package
- CUDA profiling tools
- Existing performance and reproducibility tests
- Existing checkpoint formats

Preserve unrelated user modifications.

Do not modify frozen protocols, historical evidence, original checkpoints, institutional trust stores or protected dataset artifacts.

Use:

.\.venv\Scripts\python.exe

Target hardware:

NVIDIA RTX 3060 Ti, approximately 8 GB VRAM.

## 2. End-to-end performance profiling

Implement a reproducible performance benchmark covering:

1. GlobalMedFiLM
2. FULL G/R/B/S system
3. Lite depthwise_compact G/R/B/S system
4. Five external segmentation baselines

Measure under clearly specified hardware and precision settings:

- Model initialization time
- Pure model forward latency
- Complete inference-pipeline latency
- Preprocessing and postprocessing time
- Median, p90 and p95 latency
- Throughput
- Peak CUDA allocated memory
- Peak CUDA reserved memory
- CPU memory where practical
- Inference parameter count
- Conv/linear MACs
- Conditional refiner invocation rate

Use CUDA synchronization when timing GPU operations.

Distinguish:

- Cold start versus warmed inference
- Batch size 1 versus any larger batch
- FP32 versus supported mixed precision
- Conv/linear MACs versus actual end-to-end execution time

Use multiple warm-up and measured iterations, with explicit counts in the report.

Keep workloads bounded and avoid unnecessary lengthy synthetic experiments.

Never present synthetic timing or synthetic routing behavior as real-data segmentation performance.

## 3. Evaluate conditional computation correctly

For FULL and Lite, benchmark deterministic synthetic scenarios that exercise:

- Router skip
- Router execution
- Safety accept
- Safety reject
- Forced skip
- Empty or invalid ROI handling

Measure actual branch-specific latency and computational cost.

Compare:

- Global-only execution
- Always-refine execution
- Conditional execution

Include router, feature extraction, crop, regional fusion and safety overhead in complete pipeline latency.

IMPORTANT:

Phase C observed 100% refiner activation for FULL and 0% for Lite on synthetic fixtures.

Treat these as synthetic outcomes, not expected behavior of trained models.

Do not optimize thresholds to obtain artificial performance gains.

Do not claim lower end-to-end runtime based solely on fewer refiner invocations.

## 4. GPU memory engineering

Profile actual peak allocations for:

- Global backbone forward/backward
- Regional refiner forward/backward
- Benefit router training
- Safety module training
- FULL combined inference
- Lite combined inference
- Baseline inference

Use 512×512 global inputs and the actual 256×256 ROI contract.

Test realistic batch sizes subject to GPU memory constraints.

Assess:

- Autocast
- Gradient accumulation if supported
- DataLoader worker counts
- Pinned memory
- Unnecessary tensor retention
- Repeated allocation patterns
- GPU memory cleanup between runs

Do not introduce numerical changes without documenting them and adding regression tests.

Do not globally disable determinism merely to gain benchmark speed.

If memory optimizations are optional, expose them through explicit configuration.

## 5. Verify reproducibility

Recheck the known DataLoader generator-state defect fixed in Phase B.

Verify reproducible:

- Seeding
- DataLoader ordering
- RNG capture and restoration
- CUDA algorithm selection
- Checkpoint selection
- Resume behavior
- Training-stage dependency identities
- Prediction export
- Per-image evaluation results

Test uninterrupted versus interrupted-and-resumed synthetic training.

Test uninterrupted versus interrupted-and-resumed synthetic evaluation.

Compare appropriate numeric and artifact invariants, while allowing explicitly documented nondeterministic metadata such as timestamps or resume counters.

Report where exact identity is expected and where numerical tolerance is appropriate.

Do not claim cross-device bitwise equality unless demonstrated.

## 6. Test actual FiLM conditioning functionality

The GlobalMedFiLM conditioning projections may initialize to identity.

This is permitted.

However, initialization tests alone do not prove task conditioning works after optimization.

Using only synthetic data:

1. Verify task IDs propagate through all intended FiLM blocks.
2. Verify gradients reach trainable FiLM projection parameters.
3. Verify task-conditioning parameters can update during short synthetic optimization.
4. Verify a nontrivial learned conditioning state can produce task-dependent feature or prediction differences.
5. Verify the C1 identity-FiLM control preserves its intended frozen behavior.
6. Verify unrelated architecture components are not modified by this test.

Do not alter frozen C1 training semantics.

Do not interpret synthetic task sensitivity as evidence of medical segmentation accuracy.

## 7. Full failure-recovery testing

Inject controlled synthetic failures during:

- Global training
- Cache creation
- Refiner training
- Benefit-label generation
- Router training
- Safety training
- Evaluation export
- Result publication

Verify:

- Atomic checkpoint publication
- Interrupted-run detection
- Resume from the correct stage
- Checkpoint dependency validation
- Corruption rejection
- No cross-seed contamination
- No duplicate evaluation rows
- No silent completion of partially evaluated cells
- No overwrite of valid artifacts
- No accidental acceptance of mismatched preprocessing

Any cleanup must be restricted to task-owned synthetic temporary files.

Never remove existing research outputs, trust stores or unrelated directories.

## 8. Prevent synthetic-to-real evidence contamination

This is a critical requirement.

Phase C reports:

24/24 synthetic cells COMPLETE_VALIDATED

but:

0/24 legitimate research cells established.

Enforce that separation structurally.

Test that synthetic artifacts cannot be promoted to genuine research evidence through:

- Output-directory reuse
- Registry import
- Report aggregation
- Resume
- Checkpoint substitution
- Artifact copying
- Missing or tampered evidence-class fields

Use a clear evidence namespace and integrity checks.

Real research cells must remain NOT_ESTABLISHED until genuine compatible evidence exists.

Do not change the accepted research protocol.

## 9. Dataset and evaluation boundary checks

Respect:

TRAIN5832
VAL808
TEST1683
ROUTER_HOLDOUT875
External retrospective884

Do not run protected TEST1683 inference.

Do not perform new real-data optimization or experiments.

Verify preprocessing and loader behavior using synthetic fixtures and previously permitted metadata checks.

Keep scoring outside the GT-free model inference interface.

Confirm that no performance optimization introduces oracle information or changes task-specific preprocessing.

## 10. Resource stability

Test repeated synthetic inference for:

- Unexpected CUDA memory growth
- Retained computational graphs
- Leaked file handles
- Unbounded caches
- Incomplete model cleanup
- Repeated model-loading overhead

Use a bounded number of iterations and document the measurement procedure.

Distinguish normal allocator caching from a genuine memory leak.

Do not claim production deployment readiness or clinical reliability based on synthetic stress testing.

## 11. CPU and CUDA parity

Test FULL, Lite and representative baselines on CPU and CUDA where feasible.

Record:

- Output shape identity
- Finite-value behavior
- Mean absolute probability difference
- Maximum absolute probability difference
- Binary mask agreement
- Routing decision agreement

Do not require bitwise identical CPU/CUDA output where the underlying operations do not guarantee it.

Do not choose arbitrary tolerances solely to make a failing test pass.

Where meaningful discrepancies arise, investigate and report them.

## 12. Handle the existing regression-suite limitation

The full suite previously reported:

1057 passed
1 failed
1 skipped
1 xfailed

The outstanding failure relates to the RC2 production trust-store expectation.

Do not remove or modify real institutional trust files.

Do not weaken the production security check.

You may add an isolated fixture-based test of missing-store behavior, using a temporary mock location that cannot interact with real trust material, if useful.

Keep any host-environment mismatch clearly reported.

Use a fresh, explicitly scoped pytest --basetemp directory to avoid the existing stale-temp cleanup guard.

Never bulk-delete unrelated temporary directories.

## 13. Final regression testing

Run targeted tests for:

- FULL pipeline
- Lite pipeline
- Architecture drift
- Stage 6
- Phase C evaluation
- Dataset/ROI
- Metrics and statistics
- Checkpoint recovery
- CUDA memory
- FiLM conditioning
- Evidence-class separation

Run the broad suite when feasible.

For every failure, identify whether it is:

- A new regression
- A pre-existing code defect
- A fixture defect
- An environmental issue
- An unsupported operation

Fix genuine code defects. Do not hide failed tests.

## 14. Final deliverables

Provide one concise Phase D completion report documenting:

1. Git HEAD and changed files
2. Performance benchmark methodology
3. Actual measured CPU/GPU latency
4. Memory measurements
5. FULL versus Lite conditional compute
6. FiLM gradient and conditioning verification
7. Checkpoint/resume reliability
8. Synthetic evidence-isolation tests
9. Failure-injection results
10. CPU/CUDA parity observations
11. Complete regression-test results
12. Remaining technical blockers
13. Git commit hash
14. Phase D completion decision

Keep benchmark data clearly labeled SYNTHETIC_BENCHMARK.

Do not modify the manuscript's real research results.

Commit only task-owned verified changes.

## Definition of done

Phase D is complete only when:

- All eight model adapters have reproducible profiling paths.
- FULL and Lite routing branches are benchmarked correctly.
- GPU memory use is characterized on the RTX 3060 Ti.
- Deterministic resume is demonstrated where specified.
- The FiLM conditioning mechanism is functionally verified.
- Synthetic artifacts cannot masquerade as genuine controlled results.
- Interruption and corruption recovery are tested.
- Actual new engineering regressions are resolved.
- Existing protected research restrictions remain intact.

Do not start real experiments.

Do not begin Phase E.

After completion, STOP.

TARGET:

PHASE_D_GPU_RELIABILITY_COMPLETE__DETERMINISM_VERIFIED__CONDITIONAL_COMPUTE_PROFILED__SYNTHETIC_EVIDENCE_ISOLATED__REAL_RESULTS_UNCHANGED</user_query>