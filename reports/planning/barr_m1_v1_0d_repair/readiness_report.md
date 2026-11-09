# BARR-M1 v1.0d critical engineering repair

Date: 2026-10-27 (Asia/Dhaka). Engineering result: REPAIRED.
Scientific authorization: NOT_APPROVED. Production execution: DISABLED.

**86 passed, 0 failed, 0 skipped; 86 tests total.**
The test log and machine-readable results accompany this report. All statistical
fixtures, signatures, and output bundles in these tests are synthetic. Test keys
were ephemeral in-memory keys, never installed as supervisor credentials.

## Direct comparison with the four defects

| Recorded defect | Repair | Demonstration |
|---|---|---|
| Unsigned self-asserted approval accepted | Ed25519 canonical-payload verification binds independently named signer, authorization ID/dates, scope, exact inputs, checkpoint lineage SHAs, original protocol plus erratum, exclusions and runtime bundle SHA. Production trust provider always refuses because no independent trust anchor exists. | Signed synthetic positive control; missing/unsigned/forged/untrusted/altered/expired/revoked/incomplete/wrong-scope/wrong-harness failures; synthetic signatures cannot authorize production. |
| A8 K=0 accepted | Exact frozen configuration and membership checks enforce budget 0.25, K=1239, 1205 accepted, 34 rejected; eligible IDs and domain identity are keyed. Invalid CLI/environment/config overrides fail closed. | K=0 and wrong K rejected by the actual validator; valid 4957-case fixture passes; missing/duplicate IDs, wrong population, ineligible selection and wrong partition rejected. |
| KUB cluster bootstrap incomplete | Whole patients sampled with replacement; all patient cases included with multiplicities; resampled KUB mean divides by actual sampled case count; common draws across all paired contrasts. | Unequal synthetic patient clusters, repeated-patient multiplicity, incorrect individual-case sampling rejection, reproducibility and row-order invariance. 2000 resamples, seed 42. |
| Restart handling incomplete | Deterministic binding identity, input/auth-ID/bundle-SHA binding, canonical bundle with hash receipt, OS process lock, flushed staging and atomic non-replacing commit, explicit verified-prefix recovery. | Interruptions before write, during write, before commit and after commit; identical resume; duplicate/concurrent resume handling; partial/committed corruption and conflicting outputs refused. |

The old v1.0d entrypoint is now a refusal shim. Its original bytes are retained in
`reports/planning/barr_m1_v1_0d_pre_repair_source.txt` for provenance, not execution.
The earlier three regression tests now pass, and the new suite exercises the
production validation primitives rather than predetermined pass flags.

## Deliverables and verification

- `scripts/analysis/barr_m1_v1_0d_repaired/contracts.py`: frozen constants imported
  from the hash-verified v1.0c gate without calling its real-data routines.
- `authorization.py`: Ed25519 verifier and permanently blocked production trust
  boundary for this work package. No payload, environment variable, CLI argument,
  repository key file, or test success can configure a production trust anchor.
- `analysis.py`: verified-byte CSV primitive, protected-path checks, keyed joins,
  arm validation, strict/tolerance harm, separate macro and pooled measures,
  per-case/per-domain results, paired bootstrap and pure in-memory analysis kernel.
- `storage.py`: single-bundle atomic commitment and deterministic explicit resume.
- `__main__.py` and the legacy shim: production --execute remains fail-closed.
- `tests/test_barr_m1_v1_0d_repaired.py` and updated original regression tests.
- `artifact_sha256.json`, `synthetic_test_results.json`, `synthetic_test_log.txt`.
- Pinned tested dependencies in the package's `requirements.txt`.

Reproduce synthetic tests only:

```
.venv\Scripts\python.exe -m unittest discover -s tests -p test_barr_m1*.py -v
```

The release-writing validation script refuses an existing destination. The
unittest command can be rerun without changing the frozen evidence package.

Runtime bundle SHA-256 (canonical path-to-digest map of all runtime Python files,
dependency pins, and legacy shim):
`acde29ac3d4b9f9735a5133ceecbe44fa21c64d93e2f9fa4a5345a9eec15f2fe`

The artifact manifest binds the report, tests, log, modules and preserved source;
it excludes itself. The runtime bundle hash avoids a single-file authorization
that could miss changes to an imported module. Any runtime change invalidates it.

Frozen v1.0c gate preserved: **True**.
SHA-256: `e82ecdb781a56355a9a0a1ebabd948932fee0e15e71d90770bbd0b8459e96c32`.
Original request, both erratum artifacts and scope freeze also match their
expected digests. No Phase01-40, EXT-03, Phase-25 or Phase-28 artifact was modified.
No scientific value, design, roadmap or historical report was rewritten.

## Scientific and operational boundaries

BARR-M1 remains DESCRIPTIVE_POLICY_COMPARISON, A0/A1/A8 only, ROUTER_DEVELOPMENT
n=4957, IN_SAMPLE. The primary estimands are paired equal-domain macro Dice
differences A8-A0, A8-A1 and A1-A0. The bootstrap uses 2000 resamples and seed 42.
All-population pooled means and applied-case conditional means are explicitly
separate. Harm uses both delta < 0 and delta < -1e-9, with all-population and
conditional-on-applied-policy denominators. A0's empty conditional denominator
is null, not an invented zero rate. Candidate execution, selection, application
acceptance and rejection are separate: A8 1239/1239/1205/34; A1 4957; A0 0.
Counts never come from the number of nonzero Dice deltas.

The frozen safety strings ACCEPT_REFINEMENT/FALLBACK_GLOBAL are consumed directly.
Probability-threshold comparison checks consistency only; no decision is learned
or recomputed from ground truth. Source schemas were checked against headers and
existing producer code without loading scientific arrays for computation.

The completed lineage record identifies `manifests/phase4_v3/train.csv` as the KUB
patient-ID source. Its SHA was observed during preparation and is explicitly bound
as an additional grouping input for future approval:
`28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6`.
This is not represented as an entry in the old v1.0c release manifest. A future
approved runner must verify it before parsing and join by sample_id; 267 KUB
patients are required. ISIC/BUSI/KVASIR retain NOT_AVAILABLE patient IDs and the
prespecified per-case grouping limitation. No holdout/test manifest was read.

Read the original approval request together with its separate erratum:
`reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_supervisor_authorization_request.md`
and `reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_erratum.md`.

No legitimate supervisor authorization or independent production trust anchor
has been established. The supplied environment contains old test JSON records;
these are not authority and were not accepted. Production source loading and
execution are disabled even if the isolated signature verifier succeeds.

A future deployment must establish institutional trust and revocation handling
outside repository-controlled inputs and verify a separate explicit launch
instruction. Enabling that integration changes the runtime hash and requires
approval of the resulting exact version; approval of this disabled package alone
does not make it executable. No supervisor private key was generated or installed.

Crash-recovery tests ran on the local Windows filesystem. Windows commit uses
MoveFileExW with WRITE_THROUGH and no replacement; POSIX code uses atomic hard-link
creation and directory fsync. The POSIX branch was not runtime-tested here.
The tests simulate process interruptions; they do not certify physical media
against power failure or network-filesystem semantics.

Excluded: A7-versus-A8, BARR-M2, FiLM-off training control, EXT-03B baseline training,
EXT-04 onward, training/optimizer steps, model construction, inference, TEST,
ROUTER_HOLDOUT, external evaluation, new retrospective arms. No isolated-router
causality, clinical safety, superiority or independent-generalization claim.

No real-data paired contrasts, confidence intervals or per-case scientific outputs
were produced. No model checkpoint was opened. No scientific launch command was
issued; execution refusal was tested by direct unit-test dispatch only.

## Terminal

`BARR_M1_V1_0D_ENGINEERING_REPAIRED__AUTHORIZATION_PENDING__NO_SCIENTIFIC_EXECUTION`
