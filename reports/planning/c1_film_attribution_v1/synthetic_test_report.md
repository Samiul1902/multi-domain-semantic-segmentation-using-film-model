# C1 synthetic identity-control verification report

**Scope:** CPU-only synthetic tests; no real-data scientific execution. No TRAIN/VAL CSV, image, historical checkpoint, TEST or ROUTER_HOLDOUT data were opened by these tests. The protocol file is a preparation artifact, not a dataset. No scientific trainer/evaluator was invoked.

Command from D:\Softfors\jup:

```text
D:\Softfors\jup\.venv\Scripts\python.exe -B -m pytest -q tests/test_c1_film_preparation.py -p no:cacheprovider --junitxml=<temporary-directory>/synthetic_tests.xml
```

Environment for the test invocation: PYTHONDONTWRITEBYTECODE=1, CUDA_VISIBLE_DEVICES empty, torch CPU threads1 (restored after test class). pytest9.1.1, torch2.6.0+cu124, Python3.11.9. The single targeted module was run, not the whole project's possibly data-reading test collection.

## Live outcome

**Final suite: 15 tests passed plus14 unittest subtests passed, zero failures/errors/skips; observed pytest duration3.87 seconds.** JUnit reports29 entries (tests plus subtests); exact suite duration is recorded in synthetic_test_report.json. An earlier 13-test run also passed before the additional source-drift/CLI rejection tests; the final count supersedes that test inventory, not any scientific result. No absolute creation-time claim: Windows time service was not started. Test duration is not a training benchmark or study result.

## Requirements verified

1. Each of five FiLM sites yields exactly its input tensor, with gamma=beta=0 for every task.
2. Frozen conditioning parameters receive no gradients, remain unchanged after a synthetic backbone optimizer step, and are excluded from optimizer parameter groups.
3. Control encoder/head gradients are present and the permitted backbone/head changes after one synthetic step.
4. Treatment/control initial tensors match for all predeclared seeds; helper restores caller CPU RNG. No historical checkpoint used.
5. Full synthetic control logits equal logits with FiLM sites bypassed and are invariant to all valid task IDs. Frozen-source SHA plus source inspection establishes no other task-conditioned forward pathway.
6. Treatment FiLM output projection has gradients and task conditioning remains learnable. Identity-at-init is not a statement about trained treatment weights.
7. Corrupt/nonzero output projection or unfrozen conditioning is rejected.
8. Dataset ID, version, task map, prohibited list, split, path, count or digest changes fail closed. A mocked file-read prohibition confirms metadata validation does not access datasets.
9. Absent/incomplete/BARR-M1 approval is rejected; separate launch is required. Even a fabricated complete C1 approval and launch dictionary is rejected by the hard preparation-only stop. Synthetic records exist only in test memory, not as approval files.
10. Protocol digest corruption is rejected before JSON parsing. Frozen architecture source drift blocks construction. The status CLI rejects `--execute` with argparse status2 rather than silently treating it as permission.

## Implementation-derived accounting

Both fresh models:3,523,001 total parameters,90,768 conditioning,3,432,233 non-conditioning,14,092,004 FP32 parameter bytes. C1-T trainable3,523,001/frozen0; C1-C trainable3,432,233/frozen90,768. One AdamW group per arm, lr1e-4/wd1e-4, exactly trainable tensors. Thus counts match historical expectations but were recalculated from real constructors rather than asserted as experimental outcomes.

## Limits

No synthetic 512-batch GPU training benchmark, no real-data loader integration, resume/failure simulation, cluster-bootstrap implementation or outcome analysis was run. The future C1 driver must implement/test those approved operational contracts. These tests establish **IMPLEMENTATION_READY for control/scope primitives**, not an independently validated segmentation effect, full trainer readiness, scientific approval or permission to launch. C1 remains NOT_ESTABLISHED.

Machine-readable test/accounting data are in `synthetic_test_report.json`. Artifact/source SHA-256 identities are in `package_identities.json`. Historical evidence and RC1 remain unchanged.
