# BARR-M1 execution preparation: technical verification failed

Date: 2026-10-27 (Asia/Dhaka). Approval: NOT_APPROVED. No scientific execution.

## Authoritative handoff

Read the [original approval request](barr_m1_approval_v1_0c/barr_m1_v1_0c_supervisor_authorization_request.md)
together with the [additive erratum](barr_m1_approval_v1_0c/barr_m1_v1_0c_erratum.md).
They remain separate authoritative artifacts. The existing supervisor handoff
already explains this relationship; its execution-readiness statement must not
be treated as evidence that the candidate passed engineering verification.

All four supplied SHA-256 values were verified against existing bytes:

| Artifact | SHA-256 |
|---|---|
| Erratum Markdown | 7653cefd5b1bf6a1e28e5c9f65e1850a561f7316d48226dfb0859195c1c38f45 |
| Erratum digest JSON | 22f0abd376806de3e1fa340050840992621561a4fd8d25928ccfa602679d7f12 |
| Original authorization request | a1a59cffc83e7b167b6ae28f75123167abf06d37d080e09c3cc0cdf519419a42 |
| Frozen v1.0c gate | e82ecdb781a56355a9a0a1ebabd948932fee0e15e71d90770bbd0b8459e96c32 |

These files were reused without edits. No frozen manifest, document, historical
record, numerical result, or roadmap was changed.

## Candidate and blocking evidence

A separate candidate already existed at
`scripts/analysis/barr_m1_reanalysis_execute_v1_0d.py`; it was inspected and left
unchanged. It is not technically complete. No replacement harness is claimed.

Targeted synthetic tests in `tests/test_barr_m1_preparation_blockers.py` ran via:

```
.venv\Scripts\python.exe -m unittest discover -s tests -p test_barr_m1_preparation_blockers.py -v
```

Result: 3 tests, 1 passed, 2 failed (exit 1).

- PASS: missing authorization raises AuthorizationError.
- FAIL: an entirely mocked, unsigned self-asserted approval with an invalid date
  and no exclusions is accepted when its declared digests match. No synthetic
  approval file was written. Thus unauthorized-execution protection is not
  adequate, despite rejection of a missing record.
- FAIL: synthetic matching unique IDs and the expected domain counts, but K=0,
  pass population validation and delta construction instead of failing closed.

Additional code-level blockers (not claimed as runtime test results):

- Bootstrap resamples cases in every domain; it does not implement the frozen
  KUB patient clustering requirement and does not require KUB patient IDs.
- The output manifest lacks input and output digests; writes do not implement
  deterministic interrupted-write recovery or verified restart.
- Required per-domain result output is absent; tolerance-adjusted harm rates
  are absent and pooled statistics lack explicit denominator labels.
- Several built-in tests use literal True instead of exercising failure paths.
- No separate verified launch-instruction requirement is enforced.

The frozen gate's execution branch unconditionally refuses execution on static
inspection. It was not run: its normal validation path reads real frozen arrays
and reproduces aggregates, which is unnecessary for this work order. No scientific
execution command, including an execution-mode refusal probe, was issued.

Comprehensive testing stopped after confirmed technical failures, as requested.
SHA mismatch, membership corruption, missing/duplicate IDs, ordering, wrong
population, skipped-case corruption, harm boundaries, macro/pooled aggregation,
bootstrap reproducibility, patient-ID missingness, output corruption/recovery,
and protected-access rejection are not certified by this targeted test run.

## Authorization and scientific restrictions

No valid supervisor authorization was found in the inspected BARR-M1 artifacts.
The existing root-level `tmp_fake_auth.json` and `tmp_valid_auth.json` identify
test approvers/records; filenames and matching hashes cannot establish approval.
Neither was used to authorize or launch anything.

Scope remains BARR-M1, DESCRIPTIVE_POLICY_COMPARISON, A0/A1/A8 only,
ROUTER_DEVELOPMENT n=4957, IN_SAMPLE, CPU-only frozen-array reanalysis.
Primary estimand: paired equal-domain macro Dice differences A8-A0, A8-A1, A1-A0;
2000 paired resamples, seed 42. Strict harm delta < 0 and tolerance-adjusted harm
delta < -1e-9 must both be reported. No independent-generalization, isolated router
causality, clinical safety, or model superiority claim is permitted.

A7-versus-A8, BARR-M2, FiLM-off control training, EXT-03B baseline training,
EXT-04 onward, all training/forward inference, TEST, ROUTER_HOLDOUT, external
evaluation, and new retrospective arms remain excluded. Frozen decisions must
not be recomputed from ground truth. No checkpoint was loaded.

Future launch requires verifiable supervisor/responsible-authority approval
binding study, approver, approval ID/date, exact scope/population/mode/exclusions,
approved protocol and harness hashes, followed by a separate explicit launch
instruction. A passing gate or this work order supplies neither.

STOP: technical verification failed. Harness readiness is not declared.
