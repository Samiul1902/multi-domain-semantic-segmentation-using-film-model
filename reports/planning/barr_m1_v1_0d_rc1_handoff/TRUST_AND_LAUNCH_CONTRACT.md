# RC1 trust and launch contract (unprovisioned)

This describes future institutional configuration, not permission to configure
or launch now. No registry key, trust certificate, signing key or service was
created by this work package. No production signer fingerprint is known.

## Independent machine policy

Supported production integration: 64-bit Windows, pinned Python environment,
invoked with Python -I. The fixed registry value is REG_SZ `Policy` under
`HKEY_LOCAL_MACHINE\SOFTWARE\RA-MedFiLM-BARR\BARR-M1` (64-bit view).
There is no CLI/environment/repository-file trust override. Both the product key
and BARR-M1 key must be owned by SYSTEM or BUILTIN Administrators. Allow rules
with write/delete/change-owner/change-permissions rights for any other principal
are rejected. An ordinary user must not be able to replace the policy. Privileged
machine compromise is outside what a Python signature gate can prevent.

The administrator must verify signer identity/delegation and key fingerprint by
an independent institutional channel BEFORE provisioning this value. Fingerprints
are SHA-256 of the raw 32-byte Ed25519 public key. Key material is base64(raw bytes).
The registry policy object has exactly these fields:

- environment: literal PRODUCTION
- keys: map of key_id to public_key, fingerprint_sha256, approver (real name)
- revoked_authorization_ids: list of revoked authorization IDs
- revoked_key_ids: list of revoked signer key IDs
- time_public_key and time_key_sha256: independently established time-service key
- time_url: institution-controlled HTTPS endpoint (no credentials or fragment)

The institution retains its private keys. Never create a supervisor private key
as part of this project. Synthetic test keys are ephemeral and were not installed.
Changing external machine policy is an administrative trust decision, not a source
edit. It must not be taken on the basis of this unsigned handoff alone.

## Canonical signed approval

Envelope: exactly key_id, payload, signature. Signature is base64 Ed25519 over
UTF-8/ASCII bytes from Python json.dumps(payload, sort_keys=True,
separators=(",", ":"), ensure_ascii=True, allow_nan=False). Duplicate JSON keys
and nonfinite numbers are rejected. Payload fields are exactly:

- study_identifier: BARR-M1
- classification: DESCRIPTIVE_POLICY_COMPARISON
- arms: [A0, A1, A8] in that order
- population: ROUTER_DEVELOPMENT; population_n: 4957
- evaluation_class: IN_SAMPLE
- execution_mode: CPU_ONLY_RE_ANALYSIS_ONLY
- input_shas: complete name-to-SHA map from release_identity.json inputs
- checkpoint_shas: complete checkpoint_lineage_shas from release_identity.json
- protocol_sha256 and erratum_sha256 from release_identity.json
- exclusions: exact sorted list in release_identity.json
- harness_sha256: the RC1 executable SHA (not the old v1.0d bundle SHA)
- authorization_id: unique ID assigned by the responsible authority
- authorized_by: real approver name matching independently provisioned key owner
- approval_date and expires_at: timezone-aware ISO-8601 UTC timestamps

No signed authorization template is included: the real authority must supply its
own decision and identity. A generated test record cannot establish production
trust. Changing the executable or pinned dependency bytes invalidates the approval.

## Separate later launch work order

The same envelope format applies. The key must belong to the independently
provisioned approving/delegated authorities, and must not be revoked. Its payload
has exactly:

- purpose: SEPARATE_EXPLICIT_LAUNCH_WORK_ORDER
- study_identifier: BARR-M1
- authorization_id: approved authorization ID
- authorization_sha256: SHA-256 of canonical complete approval envelope
- harness_sha256: exact RC1 executable SHA
- output_relative: reports/scientific/barr_m1_v1_0d_rc1
- execution_mode: CPU_ONLY_RE_ANALYSIS_ONLY
- work_order_id: separately issued launch ID
- issued_by: real provisioned authority name
- issued_at and expires_at: UTC ISO-8601; issue must not precede approval

This later launch record is absent. There is no standalone enable flag that can
bypass these signatures. Resume uses the same bound records; a changed record or
conflicting committed output fails safely instead of silently replacing results.

## Trustworthy time and live status

The host clock is reported unsynchronized. Its UTC is never used alone to accept
approval dates/expiry. The institution must establish an authenticated time/status
service; it is not configured and no production service call was made here.

RC1 POSTs canonical JSON containing nonce (fresh 32-byte random token as hex),
authorization_sha256 and launch_sha256 to time_url. Proxies and redirects are
not used. Response is a JSON object with exactly payload and signature, signed
by the independently provisioned time public key. Its payload echoes all three
challenge fields, adds utc (timezone-aware ISO-8601), and
`authorization_and_launch_active: true` only if the bound records are not revoked.
Any inactive/missing/incorrect signature, nonce, binding, timestamp, or round-trip
over 10 seconds refuses execution. The service must honor this live-status
contract; freshness is measured with a monotonic timer, not wall-clock UTC.

Fresh time/status is required before input loading and again immediately before
computation. Approval/launch signatures, expiry and current machine policy are
revalidated. TLS certificate checks remain enabled; an unsynchronized host may
cause TLS to fail, which safely prevents execution. Repair/certification of host
time and deployment of the institutional service remain operational requirements.

## What has and has not been validated

120 synthetic tests cover frozen repair primitives, RC1 authorization dispatch,
mocked registry/ACL and time transport, signature/nonce failures, and a complete
fabricated-array run into a temporary directory. Actual production with no registry
trust policy is rejected before source loading. No production key installation,
real signer, real time service, scientific source-load success, or actual study run
is claimed. Actual registry provisioning and live service availability require the
institution's operational checks before the later launch instruction.

Atomic commit/restart was tested on the local Windows filesystem; power-loss and
network-filesystem behavior is not certified. Use the local approved output path.
All scientific computation remains CPU-only and consumes frozen arrays/decisions.
