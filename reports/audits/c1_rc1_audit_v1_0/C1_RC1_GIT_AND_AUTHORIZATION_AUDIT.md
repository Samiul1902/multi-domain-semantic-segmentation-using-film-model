# C1 RC1 — Git Completeness and Authorization-Path Audit (v1.0)

**Study** `C1_FILM_ATTRIBUTION_V1` · **Branch** `master` · **Repository** `D:\Softfors\jup`
**Release under audit** commit `bdb0f9d` (RC1) + commit `fbc0af2` (release-bound dependency tracking)
**Release digest** `1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1`
**Manifest file SHA-256** `0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe`
**Protocol SHA-256** `531e3eb2…` (unchanged)

**Scientific execution: NONE.** No training, no inference, no real-data access, no TEST or
ROUTER_HOLDOUT access, no BARR-M1 execution, no historical checkpoint modification, no frozen
protocol modification, no activation of the production launch path.

---

## Task A — Review of the seven untracked release dependencies

All seven files were reviewed against `manifest_v2.json` and scanned for credentials, patient data,
dataset records, binaries and licensing restrictions. Contents were **not edited**.

| File | Bytes | Verdict |
|---|---|---|
| `scripts/training/phase21_common.py` | 4 178 | clean |
| `src/data/domain_balanced_sampler.py` | 3 331 | clean |
| `src/data/multidomain_dataset.py` | 5 767 | clean |
| `src/models/film/__init__.py` | 546 | clean |
| `src/models/film/global_medfilm.py` | 12 458 | clean |
| `src/training/phase20_selection.py` | 3 100 | clean |
| `src/utils/run_lock.py` | 6 239 | clean |

`ALL_SEVEN_VERIFIED: True` · `CRLF_count_in_bound_bytes: 0` for the seven at review time.
No secrets, no credentials, no patient identifiers, no dataset records, no binary payloads, no
restrictive third-party licence headers.

## Task B — Scoped tracking commit

Commit **`fbc0af2`** — `chore(research): track C1 release-bound scientific dependencies`
· 7 files changed · 944 insertions(+) · 0 deletions.
RC1 commit `bdb0f9d` was **not amended**. No other path was staged.
Staged blobs were verified against working-tree bytes and against the manifest SHA-256.

## Task C — RC1 re-verification after tracking

| Check | Result |
|---|---|
| All 33 bound hashes recomputed from disk | 33/33 match |
| Release digest recomputed independently | `1aec5e17…f93ff9c1` — unchanged |
| `RELEASE_DIGEST.txt` published value | matches recomputed |
| Frozen protocol | `531e3eb2…` — unchanged |
| Manifest file SHA-256 | `0e3f1719…61736cfe` — unchanged |
| Independent verifier (`c1_launch_release_verify.py`, imports nothing from the package) | `VERIFICATION_PASSED` |
| Freeze check (`c1_launch_release_freeze.py --check`) | `RELEASE_CURRENT` |
| `tests/test_c1_launch_release.py` | 55 passed |
| `tests/test_c1_launch_multiprocessing.py` | 13 passed (171.9 s) |
| All seven formerly-untracked sources tracked in Git | 7/7 `TRACKED` |

**Verdict: `RELEASE_IDENTITY_VALID`.** No bound byte changed; the release was not voided.

### C.1 — Git-level byte-exact reconstructibility (measured, not assumed)

Tracking the seven files makes them *stored*; it does not by itself make them *checkout-reproducible*.
Three distinct comparisons were measured:

| Comparison | Result |
|---|---|
| Working tree bytes vs manifest | **33 / 33** |
| `HEAD` blob bytes (`git cat-file blob HEAD:<path>`) vs manifest | **18 / 33** |
| Fresh checkout bytes (`git checkout-index`) vs manifest | **13 / 33** |

Host git configuration: `core.autocrlf = true`, and **no `.gitattributes` exists** in the repository.

Root cause is line-ending normalisation, acting in **both** directions:

- **18 bound sources are LF in the manifest.** `autocrlf=true` applies the smudge filter on checkout
  and injects CRLF. Example: `src/models/film/global_medfilm.py` — blob `a04ff3e6…` (12 458 B, 0 CRLF)
  becomes `8f29fa3a…` (12 755 B, **297 CRLF injected**) after a fresh checkout. All seven files
  committed in `fbc0af2` are in this group: their blobs are byte-identical to the manifest, yet a
  checkout corrupts them.
- **15 bound sources are CRLF in the manifest** but their committed blobs were normalised to LF.
  These happen to survive `autocrlf=true` checkout, but would fail on any host with
  `autocrlf=false` / `input` (e.g. Linux CI).

Consequently **no single `core.autocrlf` setting reproduces all 33 bound bytes.** The 15 normalised
blobs must be renormalised.

**Two bound sources also carry genuine uncommitted content**, independent of line endings:

- `src/data/loaders.py` — +14 lines (`collate_fn`, `sampler`, `drop_last` parameters; Phase-20 additive
  sampler support). Blob is 823 B; the manifest binds a 1 345 B working-tree file. The byte delta
  (522 B) exceeds the CR count (25), so this is a content difference, not an encoding difference.
- `src/data/transforms.py` — +14 / −5 lines. Byte delta 436 B exceeds CR count 58.

These are pre-existing in-flight Phase-20 changes, not artefacts of this mission. Because the manifest
binds working-tree bytes, a clean clone of `HEAD` cannot reproduce them by any checkout configuration.

**Minimum correction (does not change the release digest):** add `.gitattributes` with a `-text` rule
for the bound paths, run `git add --renormalize`, and commit. This rewrites 15 committed blobs but
leaves the working tree — and therefore all 33 manifest hashes and the release digest — unchanged.
Because no bound source is edited, this is a **repository-hygiene commit, not a release revision**.
It was deliberately **not** performed here: it rewrites committed history content and requires a
separately reviewed change.

## Task D — Trust mechanism audit

**Mechanism: a hardcoded, empty, module-level allowlist inside a bound source.**

`src/research/c1_film_launch/launch_gate.py` line 61:

```python
AUTHORIZED_ANCHOR_SHA256: tuple[str, ...] = ()   # Empty by design. Adding a fingerprint is a release-bound change.
```

It is a literal `tuple` of zero elements. The gate is a two-phase design:

- **Phase A** (`assert_launch_authorized`, lines 361–381) — structural validation only: release digest,
  protocol identity, approval structure/scope/arms/seeds/exclusions, populations, prohibited splits,
  budget, recovery identity, trusted time, separate launch instruction. All checks name a specific
  error code.
- **Phase B** (`_establish_trust`, line 326) — the *only* trust establishment. Its first action after
  loading the anchor file is the membership test at line 329–330:

```python
fingerprint = anchor_fingerprint(anchor["public_key_pem"])
if fingerprint not in AUTHORIZED_ANCHOR_SHA256:
    raise GateError("C1_TRUST_ANCHOR_NOT_ALLOWLISTED")
```

`_establish_trust` is invoked at line 383, after every Phase A check.

**No external provisioning path exists.** Searched all launch modules for `os.environ`, `getenv`,
`configparser`, `yaml`, `toml`, `.ini`, `.cfg`: **none**. `assert_launch_authorized` accepts no
allowlist, anchor-set or policy parameter — its keyword list is
`expected_release_digest, approval, instruction, anchor_path, budget, run_plan, recovery,
trusted_time, output_root, now`. `anchor_path` supplies the *candidate* anchor, never authority: the
candidate's fingerprint must still appear in the empty tuple.

**Behavioural confirmation** (isolated probe, executed outside the repository, no file inside the
repository written):

| Probe | Input | Outcome |
|---|---|---|
| D1 | Structurally complete, correctly scoped, **correctly signed** approval + valid anchor file | `REFUSED: C1_TRUST_ANCHOR_NOT_ALLOWLISTED` |

The probe generated an ephemeral ECDSA-P256 key, signed both the approval and the launch instruction
over canonical JSON, and satisfied every Phase A check. It was still refused.

### Answer to the required question

> **CAN THE FROZEN RC1 VALIDATE A LEGITIMATE SUPERVISOR APPROVAL WITHOUT ANY SOURCE MODIFICATION?**

**NO.**

The single legitimate mechanism — registering the supervisor's SHA-256 SubjectPublicKeyInfo
fingerprint — is the constant at line 61, which is empty. Populating it edits a **bound source**, which
changes the release digest and voids RC1. There is no configuration file, environment variable,
command-line switch or API parameter that can supply the allowlist at run time.

**Verdict: `RC1_AUTHORIZATION_PATH_NOT_ACTIVATABLE`.**

## Task E — `trusted_time` provenance

`trusted_time` is a **caller-supplied dictionary**. It is validated for *shape only*:

| Field | Check | Nature |
|---|---|---|
| `synchronized` | `is True` | self-declared |
| `source` | `in {"NTP","GPS","PTP"}` | self-declared string |
| `abs_offset_seconds` | numeric, `0 <= x <= 2.0` | self-declared |
| `measured_at_utc` | ISO-8601, `0 <= now - measured <= 24 h` | self-declared |

**No signature covers `trusted_time`.** The only signed objects are `approval` and `instruction`
(`_establish_trust`, lines 335–342); `trusted_time` appears in neither payload. Probe E2 confirmed
this directly.

Behavioural results:

| Probe | Input | Outcome |
|---|---|---|
| E1 | Attestation with fabricated `server`, extra keys `fabricated_by_caller` / `no_attestation_signature`, no signature | passes all of Phase A; refused only at Phase B |
| E3 | Attestation dated 2020, honest `now` | `REFUSED: C1_TRUSTED_TIME_UNVERIFIED` (age window works) |
| E3b | Same, with caller-supplied `now = 2020-01-01` | `REFUSED: C1_LAUNCH_ORDER_VIOLATION` |
| E4 | Self-declared `abs_offset_seconds = 1.99` | passes Phase A |
| E4b | Self-declared `abs_offset_seconds = 2.01` | `REFUSED: C1_TRUSTED_TIME_UNVERIFIED` |

**Interpretation.** The two numeric windows are enforced, but they constrain *claims*, not *facts*.
`now` is itself a caller parameter (`now or datetime.now(timezone.utc)`, line 357). E3b shows that
arbitrary time travel is blocked — because `issued_at` lives in the **signed** instruction, so moving
`now` far from it violates `C1_LAUNCH_ORDER_VIOLATION`. That bounds `now` to at most 24 h before a
signed timestamp. It does **not** authenticate the time source: an issuer who legitimately signed an
instruction can pair it with a fabricated `{"source": "NTP", "abs_offset_seconds": 0.0}` attestation
and the gate accepts it. There is no nonce, no one-shot consumption and no binding to a specific run,
so the attestation is replayable within the window.

This matters concretely on this host: `w32tm` reports `Leap Indicator: 3 (not synchronized)` with
`Source: Local CMOS Clock` and the service Stopped/Manual. A `source: "NTP"` attestation produced here
would be a **false statement that the gate accepts**. `trusted_time` is therefore **advisory metadata,
not an authenticated attestation**, and the field name overstates what RC1 establishes.

## Task F — Does the empty allowlist short-circuit deeper checks?

**Yes, within Phase B; no, within Phase A.**

Because line 329–330 precedes lines 331–342, the following are **unreachable through the production
entry point** in RC1:

- `C1_AUTHORIZATION_SOURCE_MISMATCH` (institution match, line 331)
- `C1_AUTHORIZATION_ROLE_MISMATCH` (role allowlist, line 333)
- `C1_APPROVAL_SIGNATURE_INVALID` (approval signature, line 336)
- `C1_LAUNCH_SIGNATURE_INVALID` (instruction signature, line 337)

Probe evidence — every one of these defects reports the *same* code as a legitimate approval:

| Probe | Injected defect | Outcome |
|---|---|---|
| F1 | corrupted approval signature | `C1_TRUST_ANCHOR_NOT_ALLOWLISTED` |
| F2 | approval signature absent entirely | `C1_TRUST_ANCHOR_NOT_ALLOWLISTED` |
| F3 | corrupted launch-instruction signature | `C1_TRUST_ANCHOR_NOT_ALLOWLISTED` |
| F4 | wrong institution + wrong role + bad signature | `C1_TRUST_ANCHOR_NOT_ALLOWLISTED` |

Phase A is **not** short-circuited: it runs to completion before line 383, so budget, population,
prohibited-split, recovery, trusted-time and separate-launch refusals remain diagnostic.

**Consequence.** The design is fail-closed — no input can reach the positive path — but it is
**non-diagnostic at the trust boundary**: "not yet authorized" and "forged" are indistinguishable.
`verify_detached_signature` is exercised by unit tests, but not by any reachable production path.

### F.1 — Additional finding: the allowlist is a mutable module global

`AUTHORIZED_ANCHOR_SHA256` is a plain module attribute with no immutability guard. Probe (isolated
process):

```python
lg.AUTHORIZED_ANCHOR_SHA256 = (fingerprint,)
```

| Probe | Outcome |
|---|---|
| Same fully valid approval, after in-process patch | **`ACCEPTED`** |
| Release digest after patch | **unchanged** (`1aec5e17…`) |

This contradicts the module docstring's claim that registering a key "requires editing this module,
which changes the release digest and voids the release". For a caller with in-process code execution,
the positive path is reachable with **zero file modification and zero digest change**. That is not
authorization — it is tampering, indistinguishable from it and leaving no provenance — but it means
the defence boundary is the process, not the module, and the docstring overstates the guarantee.

**Recommended correction for the next release:** make the allowlist immutable (module-level
`Final`/tuple behind a read-only accessor, or a `frozenset` produced once at import) and, preferably,
source it from a policy file that is itself bound by the manifest so that any change to it is a
digest-visible event.

## Task G — Git remote and push

| Item | State |
|---|---|
| Branch | `master` |
| Upstream | none (`fatal: no upstream configured for branch 'master'`) |
| Remotes | none (`git remote` empty; 0 `remote.*` config entries) |
| Bundles | none (`*.bundle` absent) |

**`GIT_REMOTE_CONFIGURATION_REQUIRED`** · **`GIT_PUSH_STATUS: BLOCKED`**.
Commits `bdb0f9d` and `fbc0af2` exist **only in this local repository**. There is no off-host copy and
no remote to push to. This is a pre-existing condition, unchanged by this mission; no remote was
invented and nothing was pushed.

## Task H — Final readiness decision

| # | Item | Result |
|---|---|---|
| 1 | Seven release-bound dependencies reviewed and clean | **PASS** |
| 2 | Scoped tracking commit created, RC1 not amended | **PASS** (`fbc0af2`) |
| 3 | RC1 identity re-verified, digest unchanged | **PASS** (`1aec5e17…`) |
| 4 | Tests pass | **PASS** (55 + 13 = 68) |
| 5 | Bound sources byte-exactly reconstructible from Git | **FAIL** (13/33 on fresh checkout) |
| 6 | Legitimate supervisor approval validatable without source modification | **FAIL** (`C1_TRUST_ANCHOR_NOT_ALLOWLISTED`) |
| 7 | `trusted_time` authenticated | **FAIL** (caller metadata; no signature; no nonce) |
| 8 | Trust-boundary refusals diagnostic | **FAIL** (F1–F4 collapse to one code) |
| 9 | Allowlist immutable against in-process patching | **FAIL** (mutable global) |
| 10 | Off-host durability | **FAIL** (`GIT_REMOTE_CONFIGURATION_REQUIRED`) |

Items 5 and 10 are **repository/operational** defects correctable without touching a bound source, and
therefore without a release revision (item 5 by `.gitattributes` + renormalise; item 10 by configuring
a remote).

Items 6–9 are **release-bound** defects in `launch_gate.py`. Correcting any of them edits a bound
source, changes the release digest, and voids RC1. They require a newly frozen release — provisionally
**RC2** — which is **not** created here.

The authorization path is the binding constraint: RC1 cannot validate any legitimate approval, so it
cannot be handed to a supervisor as an executable release.

**Terminal: `C1_RC1_AUTHORIZATION_PATH_BLOCKED__RELEASE_REVISION_REQUIRED__NO_SCIENTIFIC_EXECUTION`**

### Minimum technical correction set for RC2 (specified, not implemented)

1. Populate `AUTHORIZED_ANCHOR_SHA256` with exactly one fingerprint — the supervisor's SHA-256 over
   DER SubjectPublicKeyInfo — obtained out of band and recorded in the approval package.
2. Make the allowlist immutable at run time, and ideally manifest-bound, so any change is
   digest-visible.
3. Extend the signed payload to cover `trusted_time`, or remove the trusted-time claim from the gate
   and record the host clock limitation as an explicit, signed limitation instead.
4. Give the trust boundary a distinguishable refusal for "allowlisted key, bad signature" versus
   "key not allowlisted", so negative controls remain diagnostic.
5. Re-freeze: `c1_launch_release_freeze.py`, then `c1_launch_release_verify.py` must report
   `VERIFICATION_PASSED` at the new digest, and the 68 tests must be re-run.

---

## Provenance

All figures in this document were measured in this session against the repository as it exists on
disk. Bound-file hashes were read from disk, never transcribed. The release digest was recomputed
twice by two independent implementations (the package and `c1_launch_release_verify.py`, which does
not import it). Probe results were produced by an isolated script executed from outside the repository
tree, which wrote nothing inside it.

**Absolute timestamps are omitted deliberately:** the host clock is not synchronised
(`Leap Indicator: 3`, `Source: Local CMOS Clock`, `w32tm` Stopped/Manual), so no timestamp produced
here can be bound to a trusted reference.
