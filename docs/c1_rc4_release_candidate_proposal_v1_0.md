# C1 RC4 Launch Candidate — Proposal for Formal Review (DRAFT)

Status: **DRAFT. Not sealed, not published, not an authorized release. No RC5 has been created.** Institutional approval PENDING; real runs 0/6. RC1–RC4 are unchanged.

## Candidate files (task-owned, unbound)

| File | Purpose |
|---|---|
| `scripts/analysis/run_c1_campaign_launch_rc4_draft.py` | Preflight CLI; `--execute` always refused |
| `src/research/c1_rc4_candidate/campaign_rc4_draft.py` | RC4-only orchestration, per-run proofs, external trust anchor |
| `tests/test_c1_rc4_candidate_launch.py` | Synthetic acceptance and refusal tests |

`scripts/analysis/run_c1_campaign_launch.py` (RC3, with the pre-existing uncommitted edit) is untouched.

## Smallest release package that closes the gaps (proposal, for review)

A new, separately reviewed release (name to be decided under the project's release-change procedure; not created here) binding:

1. **Entry point:** the final RC4 launcher script and `campaign_rc4_draft.py`, after review. Authorization of the draft is a release-procedure decision, not a run-time edit.
2. **Gate/trust:** `rc4_gate.py`, `trust_rc4.py`, `release_identity_rc4.py`, `launch_driver_rc4.py`. These are RC4's own files, so the new release should pin the existing RC4 digest (`05a330d1…eada2`) as a predecessor instead of rebinding them.
3. **Trainer/loader:** already bound transitively via the RC1 manifest (`c1_film/*`, `src/data/*`) and re-verified live by RC4.
4. **Protocol:** `reports/planning/c1_film_attribution_v1/protocol.json`, SHA-256 `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61`.
5. **Institution's release identity:** the institution approves the new release digest in its signed approval (`release_id`, `release_digest`). The operator supplies that digest to the launcher from the approval, never hardcoded from the workspace.

Minimal delta: launcher + draft module + their tests + pinned predecessor RC4.

## Trust requirement (software policy, pending institutional decision)

- Authenticity of the policy-owner public key must be established **outside the repository and development directory**. The institution publishes the owner-key SPKI fingerprint through its official channel; the operator passes it as `--owner-key-fingerprint`. The candidate compares it with the key that signed the trust policy (`C1_RC4_EXTERNAL_ANCHOR_MISMATCH` otherwise; missing or malformed gives `C1_RC4_EXTERNAL_ANCHOR_REQUIRED`).
- Tested: an attacker-created store with plausible names and self-generated keys passes the existing location/identity-text checks (the known gap, kept as a test control) but is refused by the external anchor.
- Residual limitation: the control is only as strong as the channel that delivers the fingerprint. Windows ACLs remain advisory in the current code and were not changed.
- Signed approvals and signed time proofs are **current software-policy requirements**, not asserted legal requirements. Whether the institution requires them, or accepts another mechanism, is an institutional decision (see `docs/c1_institutional_question_set_v1_0.md`). Any relaxation needs explicit review; nothing was weakened.

## Verification (synthetic only)

`tests/test_c1_rc4_candidate_launch.py`: 16 tests covering six-run preflight with distinct single-use proofs, refusal of execution, predecessor and wrong digests, missing and legacy trust, forged/unsigned/wrong-role signatures, expired clock proof, reused nonce, unauthorized splits/runs/data access, external anchor, and synthetic checkpoint resume with recovery-identity checks.
