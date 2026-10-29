"""RA-MedFiLM-BARR C1 launch RC3 package.

RC3 is additive to RC2. It does not modify RC1 or RC2 in any way.

What RC3 adds:
    time_status_rc3.py: NTP-based host clock measurement and signed attestation.
    rc3_gate.py: RC3 authorization gate that uses effective_host_clock_trust()
                 instead of the RC2 hardcoded NOT_ESTABLISHED constant.

RC1 and RC2 are preserved exactly. Their release digests are unchanged.
"""

