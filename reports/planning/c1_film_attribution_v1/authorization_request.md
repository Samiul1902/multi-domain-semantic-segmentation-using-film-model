# C1-specific scientific authorization decision request

**Decision requested; NOT APPROVED. No approver identity, authorization or signature has been supplied.**

Question: Does learnable task-conditioned GlobalMedFiLM differ from a matched from-scratch identity-modulation control under one predeclared protocol? C1 remains NOT_ESTABLISHED. This package is unrelated to BARR-M1 RC1 approval and grants no training/inference/evaluation access.

## Proposed binding scope

- Study C1_FILM_ATTRIBUTION_V1; C1-T fresh learnable conditioning and C1-C fresh identical state with all task_embedding/film_layers parameters frozen at identity output projections. No architecture rewrite, historical weight reuse or trained-checkpoint zeroing; no Phase28 RGB-only refiner F1 substitution.
- Six fresh runs: paired seeds42/123/3407. Shared backbone initialization and epoch sampling/augmentation streams; matched canonical Phase21 loss, optimizer, selection, patience, resolution, batch, precision and augmentation. Full specification: architecture_and_protocol.md and protocol.json.
- TRAIN5832 fitting, VAL808 selection/descriptive endpoint only, documented phase4_v3 identities and domain task mapping. Exclude TEST, ROUTER_HOLDOUT, external/quarantined data, C2/C3 and BARR-M1. VAL is selection-consumed, not independent validation.
- Primary endpoint: average across fixed matched seeds of equal-domain macro paired Dice treatment-minus-control. Secondary domain Dice and IoU descriptive. Conditional paired domain-stratified bootstrap, KUB patient clusters/non-KUB cases; no n=3 seed-population inference or secondary significance claims. All outputs/failures retained.
- Limits: at most100 epochs/run, patience15 and96 cumulative active GPU-hours (cap, not estimate); single GPU run at a time with project run lock. STOP on OOM/nonfinite/scope or provenance failure; no autonomous scientific change. Resume same run only under verified state/recovery review.
- Source/executable identities: unchanged frozen GlobalMedFiLM source and canonical protocol binding; new src/research/c1_film/control.py and readiness.py, tests/test_c1_film_preparation.py, protocol.json. Exact SHA-256 values are in package_identities.json. Readiness command prints status only; it contains no scientific execution path.

## Real approval and separate launch

The accountable scientific supervisor or legitimately delegated research authority must review and explicitly approve the question, arm definitions, matching, selection-consumption claim boundary, statistical design, datasets, identities, compute/failure limits and named operator through the institution's existing documented approval channel. The implementation agent cannot supply an approver or declare its own protocol approved. No new cryptographic trust system is required by this package.

Approval must name a real authorization ID, approving person/role, documented decision and time, precise C1 scope and exclusions, protocol digest, seed/arm list and authorized executable identities. An unsigned local JSON or approved=true is not evidence of institutional approval. After real approval, a later separate work order must bind that decision to the exact executable, inputs, output namespace and launch conditions. Do not launch merely because this document exists.

## Minimum unresolved execution prerequisites

1. Scientific approval accepting or amending the predeclared protocol.
2. An additive C1 real-data driver integrating this control with approved loaders, selection, data digest/group checks, output isolation, locks and authorization; no historical trainer launch.
3. Synthetic recovery/atomic-output tests and driver semantics checks. Current unit tests establish control correctness and fail-closed preparation scope, not complete trainer correctness.
4. Clock remediation/reliability review (w32tm reports service not started), free GPU/memory reservation, storage plan, recovery plan and resource authority.
5. Explicit separate launch instruction. No protected data may be inspected to resolve any design choice.
6. Frozen dependency availability: GlobalMedFiLM source is present/hash-bound locally but untracked in current Git history. This scoped preparation commit is not a self-contained training release; exact historical source provisioning must be resolved without staging unrelated work or rewriting authority.

## Decision state

IMPLEMENTATION_READY: matched-control/scope primitives, subject to passing synthetic report.
PROTOCOL_READY: predeclared design ready for scientific approval.
AUTHORIZATION_PENDING: yes.
SCIENTIFIC_EXECUTION_NOT_STARTED: yes.
OVERALL_EXECUTION_READY: no.

**Exact next action:** supervisor reviews this single package and communicates a real scoped decision. Do not begin another governance chain or a scientific smoke test.
