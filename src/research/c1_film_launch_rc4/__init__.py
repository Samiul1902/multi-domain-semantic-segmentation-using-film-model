"""RA-MedFiLM-BARR C1 launch RC4 package.

RC4 is additive to RC1, RC2 and RC3, none of which is modified. It exists to
repair a release-identity defect: RC3 delegated authorization to the RC2 chain,
so RC3 grants carried RC2 identity and ``verify_release_rc3`` was never invoked
by the gate. RC4 binds and re-verifies its own identity at mint time and again
at every grant use, and it targets a new institutional trust root (DECISION_I).

RC4 ships no trust store, no key, no approval and no clock attestation.
"""
