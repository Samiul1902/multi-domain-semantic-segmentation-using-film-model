# C1 RC4 Launch-Path Review v1.0

Reviewed commit: `855cb25`. No training, no real data opened, no production credentials. Institutional approval: PENDING. Real runs: 0/6.

## Verdicts

| Item | Result |
|---|---|
| RC4 own identity (`verify_release_rc4`, `rc4_gate._verify_release`) | Verified; RC1–RC3 digests/ids rejected (`C1_RC4_PREDECESSOR_IDENTITY_REJECTED`); manifest ↔ published digest consistent; protocol SHA-256 unchanged |
| Grant re-verification | `RC4Grant._reverify` runs at `authorize_trainer`, `authorize_loader`, `authorize_launch`; `Trainer.__init__` and `real_loader_factory` call these, so both boundaries re-check RC4 identity, trust policy, revocation and clock |
| Training/loader/model code coverage | Bound via RC1 manifest (33 files incl. `c1_film/*`, `src/data/*`), re-verified live by RC4 |
| Real entry point | **Still RC3** (see D1) |
| Trust root independent of contaminated store | Path-independent: legacy root refused before any read. **Not cryptographically pinned** (see D3) |
| RC2 `test_default_production_store_is_absent` | Environment-dependent: passes 4/4 with the default root pointed at an absent temporary path; fails only because `C:\ProgramData\InstitutionalC1Trust` now exists. Not a security regression. Real store untouched |

## Verified call chain of `scripts/analysis/run_c1_campaign_launch.py` (uncommitted edit, untouched)

`execute_campaign` → `launch_driver_rc3.launch` → `mint_rc3_grant` → RC2 validation (RC2 digest compare). It hardcodes `FROZEN_RC3_RELEASE_DIGEST`, defaults to `C:/ProgramData/InstitutionalC1Trust` (legacy contaminated store), preflights `c1_rc3_host_clock_attestation.json` there, and reuses one time proof for all six runs (second run hits nonce replay).

## Defects

- **D1 (integration gap):** launcher uses RC3 and the legacy store; RC4 is unreachable from the production entry point.
- **D2:** the launcher is in no release manifest, so it is not release-integrity covered.
- **D3:** institutional trust anchoring is location-only. On Windows `assert_policy_owner` is "ADVISORY_WINDOWS" (path under ProgramData), and no institution-published owner-key fingerprint is pinned. A store created under the OS-scope path with plausible names loads (test `test_known_gap_attacker_store_under_programdata_with_plausible_names`, marked `expectedFailure`). Attackers who only edit the workspace/manifest/digest cannot forge institutional approval: approval signatures bind the release digest, and non-production store paths are refused with `require_owner=True`.
- **D4 (design note):** `Trainer` accepts any duck-typed grant; protection relies on bound code plus the institution-signed release digest.

## Proposed minimal fix (not applied; frozen RC4 is not mutated)

Via the project's release-change procedure (a new, separately reviewed release, since the launcher and trust code must be manifest-bound):
1. New RC4-only launcher calling `launch_driver_rc4.launch`, default store `trust_rc4.PRODUCTION_ROOT`, one fresh signed time proof per run, release digest supplied from the institution-issued approval (not hardcoded from the workspace).
2. Require an institution-supplied owner-key SPKI fingerprint (out of band, recorded in the approval) matched against `policy_owner_public_key_pem`, and verify the directory ACL (admin-only write) on Windows.
3. Bind the new launcher in the new manifest.

## Evidence

`tests/test_c1_launch_rc4.py` (25) and `tests/test_c1_rc4_launch_path_review.py` (9 pass, 1 expected failure documenting D3): synthetic keys only, temporary directories.
