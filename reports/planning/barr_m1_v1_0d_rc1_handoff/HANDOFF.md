# BARR-M1 RC1: supervisor handoff

**NOT APPROVED. Production inactive. No scientific execution.**

Under one frozen fusion rule and development population, how do complete policies
A0, A1 and A8 differ in equal-domain macro Dice and harmful-refinement behaviour?
This is a descriptive policy comparison, not isolated router or safety causality.
ROUTER_DEVELOPMENT n=4957 is IN_SAMPLE; no independent-generalization, clinical
safety or superiority claim is permitted.

Read the [original request](original_approval_request_v1_0c.md) **together with**
the [existing erratum](erratum_v1_0c.md). Both copies are byte-identical to the
separate authoritative originals. Then review the [RC1 authorization request](SUPERVISOR_AUTHORIZATION_REQUEST.md).
No frozen scientific evidence or previous release was edited.

## Exact executable identity

`scripts/analysis/barr_m1_release_candidate_v1_0d_rc1.py`

SHA-256: **`1021c9b2b73227b6401d46000f7d108bd8e577cbcf6901f61d88f23fab4b1af8`**

RC1 pins the unchanged v1.0d runtime dependencies and frozen v1.0c gate. The
[release identity](release_identity.json) lists each pin, protocol/input digest,
checkpoint lineage identity and population. Any executable or pinned dependency
change invalidates this candidate and requires fresh testing and authorization.

The old v1.0d runner has an unconditional lock and cannot be activated without
source edits. It remains unchanged. RC1 can be enabled **without source edits**
only after independent administrator-provisioned trust, a valid signed supervisor
approval, a fresh signed time/revocation response, and a later separate signed
launch work order. None was installed or issued in this work package.

## Evidence

**120/120 synthetic tests pass: original 86 + RC1 34; zero failures/skips.**
All 20 entries in the previous repair manifest/preservation map still match.
See [test results](synthetic_validation.json) and [test log](synthetic_validation.log).

| Requirement | Actual validation exercised |
|---|---|
| Unsigned/untrusted authorization | Ed25519 verifier, production guard, fake approved=true, wrong key/signature/scope/harness, absent machine policy |
| A8 K=1239 | Frozen config and actual population/delta validators reject K=0/wrong K; 1205 accepted and 34 rejected enforced |
| KUB clustering | Whole-patient draws with multiplicity, unequal cluster sizes, split-cluster rejection, paired seeded reproducibility |
| Atomic/idempotent outputs | Actual local Windows commit/resume functions; four interruption points, corruption, conflicts and concurrent resume |
| Frozen input SHAs | Verified-byte parser plus RC1 loader rejects corrupted fabricated bytes before parsing; approval binds exact SHA map |
| Equal-domain macro Dice | Four-domain equal-weight function and pooled-substitution rejection; same estimator used in bootstrap |
| Protected-data exclusion | Actual path/population validators reject TEST/HOLDOUT/external/checkpoint attempts without accessing those datasets |

Positive signing tests use ephemeral keys in isolated test processes, mocked
machine/time services and fabricated arrays; output lives only in temporary
folders. Production with no legitimate anchor refuses before scientific inputs.
No real-data contrast, bootstrap estimate or per-case output was produced.

## Remaining requirements and next supervisor action

The responsible research authority must identify themselves, review the request
plus erratum and exact executable/input identities, and return a signed approval
or rejection through their established institutional channel. Their public-key
fingerprint must be confirmed independently and provisioned by a trusted machine
administrator; the authorization payload cannot establish its own trust anchor.
No responsible person's identity, authorization ID, signature or private key has
been invented here. See [trust and launch contract](TRUST_AND_LAUNCH_CONTRACT.md).

**Time limitation:** the host clock is reported unsynchronized and has not been
certified. RC1 never uses host UTC alone to validate approval/expiry; it requires
a fresh nonce-bound response from an independently trusted signed time/revocation
service. That service is not configured. TLS may also fail until host timekeeping
is repaired; such failure refuses execution. These remain operational prerequisites,
not evidence of authorization.

A valid approval is still **not a launch instruction**. A later separate work
order must bind the approval, executable and fixed output destination. Do not
launch from this handoff.

`BARR_M1_RELEASE_CANDIDATE_FROZEN__AWAITING_INDEPENDENT_SUPERVISOR_AUTHORIZATION__NO_EXECUTION`
