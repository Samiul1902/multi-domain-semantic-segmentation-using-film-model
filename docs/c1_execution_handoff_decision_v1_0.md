# C1 execution handoff — one decision required

**Study** `C1_FILM_ATTRIBUTION_V1` · **Release under review** RC3
`54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f`
**Written** 2026-10-31 · **Status** `AWAITING_OPERATOR_DECISION`
**Nothing here authorises training. No grant was minted, no nonce consumed, no dataset opened.**

---

## 1. Scientific status, stated plainly

C1 is **`NOT_ESTABLISHED`**. No C1 arm has been trained, so the frozen endpoint has never been
evaluated:

> `seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL`

seeds `{42, 123, 3407}`, equal-domain macro Dice, paired against the FiLM-off control on the
selection-consumed VAL808. This is a statement about missing evidence, not about a negative result.
C2 (BARR router + safety) remains `NOT_ESTABLISHED` as a causal claim; the external 884-case study is
`RETROSPECTIVE_EXTERNAL_STRESS_TEST` and cannot stand in for it. C3 remains `NOT_ESTABLISHED`.

The scientific recipe is frozen and **is not in question here**. `protocol.json`
`531e3eb2…087a61`, `recipe_digest` `275f20a9…81f14c`, architecture `a04ff3e6…31d11f`,
dependency lock `b4cdea3a…b0b36d`. All three are tracked in Git. None of them needs to move.

## 2. Why execution is blocked — two independent defects

**Blocker A — RC3 cannot accept its own identity.** The gate refuses the digest it was built to
authorise:

```
mint_rc3_grant(expected_release_digest = 54d1273a…3549f)
    -> C1_RC2_RELEASE_DIGEST_MISMATCH
```

`mint_rc3_grant` delegates to `rc2_mint_grant`, which calls `verify_release_rc2`, which requires
`release_id == RC2_RELEASE_ID`. So the only digest that can ever be minted is **RC2**
`54794efc…a5e737ed`. `RC3_RELEASE_ID` and `RC2_FROZEN_DIGEST` are dead constants;
`verify_release_rc3` is never called by the gate or the driver; and `RC3Grant.authorize_trainer` never
checks `release_digest` at all. The RC3 digest is decorative, and the sole accepted path is an
**identity downgrade to RC2** — the exact inverse of the intended direction.

This must **not** be repaired by editing RC3 in place. Editing a bound file voids the release, and a
gate patched to accept its own digest proves nothing about the release it is meant to guard.

The defect is not merely present, it is **untested**. `tests/test_c1_launch_rc3.py` (27 tests, all
passing) exercises `mint_rc3_grant` exactly once, and passes `expected_release_digest="INVALID_DIGEST"`
— a refusal of a garbage digest. No test ever presents the release with **its own** digest, which is
the one case the gate has to get right. Any successor revision must carry that test, and it must fail
against RC3's logic.

**Blocker B — the trust material is contaminated.** `C:\ProgramData\InstitutionalC1Trust` was created
on 2026-10-30 10:54 by RC3 provisioning, which generated **all four role keys in a single process**
and signed the policy, approval, instruction and attestation itself. Consequences:

- The root of trust is **self-referential** — the binding carries the owner public key that signs the
  policy, so one party both defines and satisfies the trust condition.
- The store owner is the researcher, with `FullControl`; `BUILTIN\Users` holds **`Write`** on the
  directory (re-verified by ACL read on 2026-10-31). The administrative separation the design
  documents is **absent in fact**. The store itself holds `c1_rc2_binding.json`, `policy.json` and
  `c1_rc3_host_clock_attestation.json`; the approval, instruction, budget, recovery and time-status
  documents sit in `configs/c1_operator/`.
- No private key persisted (the keys were ephemeral), so the material is inert twice over: every
  envelope fails `C1_RC2_SIGNATURE_INVALID`, because the script signs the inner payload while the
  verifier canonicalises the envelope minus `signature`.

The NTP measurement inside that exercise was genuine. Everything around it was not independently
witnessed. The store must be preserved as evidence, not repaired.

**Separately owed:** O8. `w32tm` reports `Leap Indicator: 3(not synchronized)` with `Source: Local
CMOS Clock` and no successful synchronisation ever recorded; the RTC was once 5.19 days behind.
`host_clock_trust = NOT_ESTABLISHED` unconditionally, so production training is refused
`C1_RC2_HOST_CLOCK_UNVERIFIED` regardless of the two blockers above. CMOS battery, UPS and a working
NTP source must be resolved before any launch.

## 3. The decision

> **DECISION R — adopt a declared researcher-operated execution model.**
>
> Stop representing C1 execution as institutionally separated. Execute under an explicit
> single-operator declaration that names the operator, records that **no institutional separation is
> claimed**, and binds the run to the frozen recipe by digest. The trust store stops being a
> *precondition* of the gate and becomes a *declared absence*, recorded in the release identity
> alongside the study, so that no reader can mistake the run for one with independent oversight.

**Why this and not institutional re-provisioning.** Re-provisioning (Option I: a genuinely separate
key custodian provisions the store and signs the policy) is the only route that would make the
separation claim true. It is also outside the researcher's control: it requires a second party with
signing authority, and it requires that party to hold the keys the current store never persisted. If
such a party exists, Option I is strictly better and this document should be rejected. Decision R is
the honest fallback when no such party exists — it converts a false claim into a true one.

**What R requires before it may be implemented:**

1. **Licence and ethics confirmation.** Each dataset used for C1 training and evaluation must permit
   the intended use under its own terms, and any ethics approval must cover execution by this
   operator without institutional oversight. **If either condition fails, R is not available and C1
   cannot execute at all.** This document cannot establish either condition and does not assume it.
2. **O8 closed** — synchronised clock, UPS enumerated, CMOS battery replaced.
3. **A new release identity.** R cannot be expressed inside RC3 without editing RC3, which is
   forbidden. It requires a **new additive revision** whose gate (a) verifies its own digest rather
   than delegating to RC2, (b) carries the operator declaration and the declared-absence record,
   (c) refuses to mint a grant whose digest does not match its own, and (d) ships a test that presents
   the release with its own digest and asserts acceptance — the case RC3 never tested.
   **This document does not create that revision.** Creating it is a separate, reviewed change.
4. **The contaminated store quarantined**, not deleted, and excluded from the new gate's search path.

**What R does not change:** the endpoint, the three seeds, the equal-domain macro Dice aggregation,
the paired structure, the 10,000-draw prespecified bootstrap, the protected TEST split, the frozen
architecture, the frozen recipe digest, or the `NOT_ESTABLISHED` status that persists until the
endpoint is actually evaluated.

## 4. What this document is not

It is not an approval, a grant, a credential, or a launch. It does not create RC4, does not write to
the production trust store, does not touch any RC1/RC2/RC3 bound file, and does not authorise a single
forward pass. It records one decision for the operator to accept or reject, and the conditions under
which accepting it would become legitimate.

---

**Operator decision:** `ACCEPT_R` / `REJECT_R_AND_PURSUE_INSTITUTIONAL_PROVISIONING` / `HOLD`

**Name / date:** ______________________________

Terminal: `C1_EXECUTION_DECISION_DOCUMENTED__AWAITING_OPERATOR__NO_LAUNCH`
