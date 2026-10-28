# C1 RC2 — Git Reconstruction and Authorization Repair (Final Report)

**Study** `C1_FILM_ATTRIBUTION_V1` · **Repository** `D:\Softfors\jup` · **Branch** `master`
**RC1 (historical, unchanged)** digest `1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1`
**RC2 (new, frozen)** digest `54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed`

**Scientific execution: NONE.** No real-data training, no inference or evaluation, no TEST or
ROUTER_HOLDOUT access, no BARR-M1 execution, no change to the frozen C1 protocol or the model
training methodology, no fabricated signature, trust anchor or approval, no automatic launch, and
no scientific approval artifact created on a supervisor's behalf.

---

## 0. Starting-state discrepancy (disclosed, not concealed)

The mission specified expected starting HEAD `fdf13a1cf4e4a56e5c66140599188191aafe5aa6`. Actual HEAD
on arrival was **`0253a39`** — `chore(research): preserve exact C1 release bytes in Git` — one commit
further on, with `fdf13a1` confirmed as its ancestor.

An earlier interrupted run had already executed Mission A. Rather than create a duplicate commit, the
existing work was **verified against the A3 acceptance criteria** and found correct. No history was
rewritten and no duplicate commit was made.

---

## 1. Mission A — Git reconstruction

### 1.1 Phase-20 approved files (operator-supplied hashes)

| File | Approved SHA-256 | Actual | Match |
|---|---|---|---|
| `src/data/loaders.py` | `EB0C1B5D…20A8F1A` | `EB0C1B5D295D3B77B3E9745FCDEB4FF93F985FD7A58FC8909D8098B5820A8F1A` | **YES** |
| `src/data/transforms.py` | `09FCFF48…C8CF8BD1` | `09FCFF4887FF8CDA4DAA215EFAD1D504D4D61F70982262022B6C2A30C8CF8BD1` | **YES** |

Both matched exactly, so the mandated STOP condition did not trigger. The working-tree versions were
tracked as they stood; their content was not edited.

### 1.2 `.gitattributes`

A minimal file with **explicit anchored `-text` rules only** — one per release-bound path. No
repository-wide normalisation rule was introduced, so unrelated files keep their existing behaviour.

* 33 rules for the RC1 bound sources (commit `0253a39`)
* 11 rules for the RC2 package (commit `e5800c0`) — 9 bound sources plus `manifest_rc2.json` and
  `RELEASE_DIGEST_RC2.txt`

The RC2 rules were **required by B4.8** (byte-exact clean-checkout reconstruction of the new release)
and are flagged here as an extension of the same mechanism beyond the literal 33 paths, for operator
review. They change no file content.

### 1.3 Reconstruction results

| Configuration | RC1 (33 sources) | RC2 (9 sources) |
|---|---|---|
| HEAD blob identity | 33/33 | 9/9 |
| `core.autocrlf=true` clean checkout | **33/33 PASS** | **9/9 PASS** |
| `core.autocrlf=false` clean checkout | **33/33 PASS** | **9/9 PASS** |
| `core.autocrlf=input` clean checkout | **33/33 PASS** | **9/9 PASS** |

Before this mission the same test produced **13/33**. Both releases are now byte-exactly
reconstructible under every supported line-ending configuration.

### 1.4 Preserved identities

| Identity | Before | After | Status |
|---|---|---|---|
| RC1 release digest | `1aec5e17…f93ff9c1` | `1aec5e17…f93ff9c1` | unchanged |
| RC1 manifest SHA-256 | `0e3f1719…61736cfe` | `0e3f1719…61736cfe` | unchanged |
| C1 protocol SHA-256 | `531e3eb2…` | `531e3eb2…` | unchanged |
| Architecture SHA-256 | `a04ff3e6…` | `a04ff3e6…` | unchanged |

Unrelated pre-existing working-tree modifications (1,152 entries) were left untouched; only exact
task-owned paths were staged.

---

## 2. Mission B — RC2 authorization repair

RC2 is a **new, additive package** at `src/research/c1_film_launch_rc2/`. RC1 is not edited; RC2
pins RC1's manifest bytes and release digest, and additionally re-verifies RC1's own identity, so RC2
fails if the historical release is no longer reproducible.

### 2.1 B1 — Independent, authenticated trust

RC1's defect was a hardcoded empty tuple of approval-key fingerprints inside a bound source: the
positive path was unreachable and provisioning required a source edit.

RC2 replaces this with an **external institutional trust store** at a fixed OS-scope path
(`%ProgramData%\InstitutionalC1Trust` on Windows, `/etc/institutional-c1-trust` elsewhere) — outside
the repository by construction:

* `c1_rc2_binding.json` — deployment binding: owner identity, policy relative path, policy digest,
  policy-owner key id and public key.
* `<policy>.json` — the trust policy, **signed by the policy owner**, listing approval keys with
  roles, status and revocation.

Because the policy is signed data, adding, rotating or revoking an approval key is an institutional
data operation that requires **no release revision**. RC2 ships no trust keys and no policy:
production is unprovisioned and the gate is fail-closed.

Refusals are now **diagnostic**. RC1 collapsed every trust failure into
`C1_TRUST_ANCHOR_NOT_ALLOWLISTED`; RC2 distinguishes `SIGNATURE_KEY_UNTRUSTED`,
`SIGNATURE_KEY_REVOKED`, `SIGNATURE_KEY_ROLE`, `SIGNATURE_INVALID` and
`TRUST_POLICY_SIGNATURE_INVALID`.

**Honest limitation, stated rather than papered over.** A Python module cannot resist arbitrary
in-process code execution — a caller who can run code here can patch anything, and `tuple`/`frozenset`
are not immutability guarantees against that. The defence boundary is OS ownership/ACLs plus
institutional provisioning. On Windows this module can only *location*-check the store
(`owner_enforcement="ADVISORY_WINDOWS"`); actual ACLs must be applied by the OS administrator and are
declared as a provisioning requirement, not a guarantee.

### 2.2 B2 — Trusted time

RC1 accepted an unsigned, caller-declared `trusted_time` dictionary. RC2 refuses that shape entirely
and requires a signed `C1_RC2_TIME_STATUS` proof that is:

* **attributable** — signed by a key the policy authorises for `TIME_AUTHORITY`;
* **bound** — to the release digest, the authorization id and the launch id;
* **single-use** — a 32+ character nonce checked against a durable on-disk ledger
  (`c1_rc2_output/nonce_ledger.jsonl`, `O_CREAT|O_APPEND`, full-write loop, `fsync`);
* **fresh** — 300 s maximum age, with an explicit issuance/expiry window and a 5 s skew allowance.

**Host clock truth is explicitly *not* established.** A signature over the sentence "the time is X"
makes the sentence attributable, not true. `host_clock_trust` is `NOT_ESTABLISHED` unconditionally,
and `authorize_trainer` refuses production training while it is not `VERIFIED`. The Windows clock was
not modified, and no time attestation was fabricated.

### 2.3 B3 — Synthetic isolation

Grants carry an `authorization_class`. A grant minted against a non-production trust store is
`SYNTHETIC_TEST`, and it is refused by **both** `authorize_trainer`
(`C1_RC2_SYNTHETIC_GRANT_CANNOT_TRAIN`) and `authorize_loader`
(`C1_RC2_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA`). The second refusal matters because
`real_loader_factory` reaches the real datasets through `authorize_loader`: without it the positive
test path could have touched real data even without training.

### 2.4 B4 — Verification results

| Check | Result |
|---|---|
| RC2 authorization tests (positive + negative) | **43 passed**, 0 failed |
| RC1 CPU synthetic suites | **89 passed**, 23 subtests passed |
| CUDA synthetic verification | **22 / 22 PASS**, 0 blocked |
| Windows multiprocessing recovery | **13 passed** (183.5 s) |
| Independent RC2 verifier (imports nothing from the package) | `VERIFICATION_PASSED` |
| Freeze check | `RELEASE_CURRENT` |
| Byte-exact clean checkout, 3 autocrlf settings | RC1 33/33, RC2 9/9 under each |
| RC1 identity preserved | unchanged |

**Positive synthetic path:** a dedicated test-only authority (ephemeral ECDSA-P256 keys, generated at
run time, never committed) produces a binding, a signed policy, a signed approval, a signed launch
instruction and a signed time proof. The full chain validates and returns
`authorization_class = SYNTHETIC_TEST`, `host_clock_trust = NOT_ESTABLISHED`, and a consumed nonce.
The resulting grant is then proved unable to train or open a real loader.

**Negative controls exercised** (all refused, each with its own code): invalid approval signature;
absent signature; invalid instruction signature; untrusted signing key; revoked signing key; wrong
role; policy content tampered with a recomputed digest; policy-owner key substituted; missing policy
file; expected-digest mismatch; approval bound to another release; RC1-style unsigned `trusted_time`;
time-proof bad signature; time-proof wrong identity binding; expired proof; stale proof; future
proof; **replayed proof** (also across process-state reset, proving the ledger is on disk);
revoked authorization; time proof signed by a non-time-role key; wrong arms; wrong seeds; prohibited
`TEST` split; budget violation; duplicate logical run; invalid recovery identity; scope mismatch;
protocol mismatch; missing separate launch instruction; direct `RC2Grant` construction.

### 2.5 RC2 release identity

```
release_id           = C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2
release_digest       = 54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed
manifest_sha256      = f5169cedce9896da5eeb78866dd36571f81fc11822b64e718235e438b397f71c
bound_source_count   = 9
supersedes           = 1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1
protocol_sha256      = 531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61
trust_store          = EXTERNAL_INSTITUTIONAL_UNPROVISIONED
host_clock_trust     = NOT_ESTABLISHED
scientific_execution = NOT_AUTHORIZED
```

Non-circular by construction: the manifest never binds itself; the digest is
`sha256(canonical_json(manifest))`; required coverage is declared **in code**, so a manifest that
omits a module fails rather than appearing complete.

---

## 3. Mission C — Git maintenance

| Item | Value |
|---|---|
| Commit — RC1 byte preservation (pre-existing) | `0253a39` |
| Commit — RC2 byte preservation | `e5800c0` |
| Commit — RC2 implementation and freeze | `55c90c3` |
| RC1 commit `bdb0f9d` amended | **No** |
| History rewritten / force-pushed | **No** |
| Secrets screen (11 files) | 0 hits — no keys, tokens, patient data, datasets or binaries |
| Largest committed file | 25,889 B (test module) |
| **GIT_REMOTE** | `NONE` (0 remotes, no upstream) |
| **GIT_PUSH_STATUS** | **BLOCKED** |
| Blocker | `GIT_REMOTE_CONFIGURATION_REQUIRED` |

No remote was invented or configured. All three commits exist **only in this local repository**. Per
`.clinerules/01-git-commit-and-push-policy.md` rule 7, the successful scoped local commits are
retained and the push is reported blocked rather than silently omitted.

---

## 4. Remaining external requirements

RC2 provides the *mechanism*. It does not and cannot supply the *authority*. Launching science still
requires all of the following, none of which this mission created:

1. **Trusted authority.** An institution must provision the OS-scope trust store — a binding plus a
   policy signed by the policy owner — listing the supervisor's key with the `SUPERVISOR` role.
   RC2 ships none of this; production trust is unprovisioned.
2. **Genuine scientific approval.** A supervisor must sign an approval scoped to
   `C1_FILM_ATTRIBUTION_V1`, bound to the RC2 release digest, for arms `C1-T`/`C1-C` and seeds
   `42/123/3407`, excluding `TEST`, `ROUTER_HOLDOUT`, `EXTERNAL`, `QUARANTINE`, `BARR-M1`, `C2`, `C3`.
   **No approval artifact was created here.**
3. **Clock.** Host time must be independently verified — O8 (CMOS battery, UPS, NTP). `w32tm` still
   reports `Leap Indicator: 3 (not synchronized)` with `Source: Local CMOS Clock` and the service
   Stopped/Manual. Until this is resolved, `authorize_trainer` refuses production with
   `C1_RC2_HOST_CLOCK_UNVERIFIED`.
4. **Power.** No UPS is enumerated; Kernel-Power 41 events total 85 in the log (0 since the current
   boot). Unremediated.
5. **Separate launch instruction and time proof.** Both must be signed, identity-bound and single-use.
6. **Clean-install dependency verification** remains unverified (104-package lock, 15 direct).

---

## 5. Terminal

```
C1_RC2_GIT_RECONSTRUCTIBLE__RELEASE_FROZEN__EXTERNAL_AUTHORIZATION_PENDING__NO_SCIENTIFIC_EXECUTION
```

---

## Provenance

Every hash in this report was read from disk or from the Git object store at the time of writing;
none was transcribed. The RC2 digest was recomputed by two independent implementations — the package
and `scripts/verification/c1_launch_rc2_verify.py`, which imports nothing from it. Absolute timestamps
are deliberately not asserted: the host clock is not synchronised, so no timestamp produced here can
be bound to a trusted reference.
