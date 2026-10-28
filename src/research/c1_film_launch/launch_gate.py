"""C1 launch authorization gate. Fail-closed by construction.

Two-phase design
----------------
**Phase A — structural validation (no trust required).** Every check here is a
pure comparison of supplied records against the frozen protocol and the verified
release identity. Phase A never consults a trust anchor, so each refusal names a
*specific* defect (wrong scope, wrong arms, wrong seeds, prohibited split,
budget, recovery identity, trusted time, launch instruction). This keeps negative
controls diagnostic instead of collapsing every failure into "untrusted".

**Phase B — trust establishment.** The approval and launch instruction must be
signed by a key whose SHA-256 fingerprint is listed in
``AUTHORIZED_ANCHOR_SHA256``.

That allowlist is **empty in this release**, deliberately. Consequences:

* No local dictionary containing ``approved=true``, an institutional name, or a
  signature-shaped string can authorize execution — those never reach Phase B
  meaningfully, and Phase B cannot pass without an allowlisted key.
* A synthetic or operator-generated key pair cannot become production authority,
  because registering it requires editing this module, which changes the release
  digest and voids the release.
* The positive path is provably unreachable in this release. A future reviewed
  release must add exactly one fingerprint here.

``assert_launch_authorized`` is the only way to mint a ``LaunchGrant``, and
``LaunchGrant`` re-verifies the release identity on every use so that a release
tampered with after authorization is rejected.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import release_identity as rid

STUDY_ID = rid.STUDY_ID
PROTOCOL_SHA256 = rid.PROTOCOL_SHA256

APPROVED_ARMS = ("C1-T", "C1-C")
APPROVED_SEEDS = (42, 123, 3407)
REQUIRED_EXCLUSIONS = frozenset({"TEST", "ROUTER_HOLDOUT", "EXTERNAL", "QUARANTINE",
                                 "BARR-M1", "C2", "C3"})
REQUIRED_APPROVAL_FIELDS = ("authorization_id", "authorized_by", "institutional_role",
                            "decision_record", "authorized_at", "scope",
                            "protocol_sha256", "release_digest")

MAX_EPOCHS = 100
MAX_CUMULATIVE_ACTIVE_HOURS = 96
LOGICAL_RUNS = 6
MAX_TRUSTED_TIME_OFFSET_SECONDS = 2.0
MAX_TRUSTED_TIME_AGE_HOURS = 24
TRUSTED_TIME_SOURCES = frozenset({"NTP", "GPS", "PTP"})

# Empty by design. Adding a fingerprint is a release-bound change.
AUTHORIZED_ANCHOR_SHA256: tuple[str, ...] = ()

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


class GateError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Trust primitives (independently unit-testable; never sufficient on their own)
# --------------------------------------------------------------------------- #
def _public_key(public_key_pem: str):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    try:
        return load_pem_public_key(public_key_pem.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise GateError("C1_TRUST_ANCHOR_KEY_UNREADABLE") from exc


def anchor_fingerprint(public_key_pem: str) -> str:
    """SHA-256 over DER SubjectPublicKeyInfo — the identity used in the allowlist."""
    from cryptography.hazmat.primitives import serialization
    key = _public_key(public_key_pem)
    der = key.public_bytes(serialization.Encoding.DER,
                           serialization.PublicFormat.SubjectPublicKeyInfo)
    return rid.sha256_bytes(der)


def verify_detached_signature(public_key_pem: str, payload: dict, signature_b64: str) -> bool:
    """ECDSA-P256/SHA-256 detached signature over canonical JSON. Never raises.

    The ``signature`` key is excluded from the signed payload, so a record can
    carry its own signature without a circular definition.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    if not isinstance(payload, dict):
        return False
    signed = {k: v for k, v in payload.items() if k != "signature"}
    try:
        signature = base64.b64decode(signature_b64, validate=True)
    except (binascii.Error, ValueError):
        return False
    try:
        key = _public_key(public_key_pem)
    except GateError:
        return False
    if not isinstance(key, ec.EllipticCurvePublicKey):
        return False
    try:
        key.verify(signature, rid.canonical_json(signed), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False
    return True


def load_trust_anchor(anchor_path: Path) -> dict:
    path = Path(anchor_path)
    if not path.is_file():
        raise GateError("C1_TRUST_ANCHOR_MISSING")
    try:
        anchor = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise GateError("C1_TRUST_ANCHOR_UNREADABLE") from exc
    for field in ("institution", "public_key_pem", "authorized_roles",
                  "valid_from", "valid_until"):
        if not anchor.get(field):
            raise GateError("C1_TRUST_ANCHOR_INCOMPLETE")
    if not isinstance(anchor["public_key_pem"], str):
        raise GateError("C1_TRUST_ANCHOR_INCOMPLETE")
    return anchor


# --------------------------------------------------------------------------- #
# Run identity
# --------------------------------------------------------------------------- #
def run_identity(release_digest: str, arm: str, seed: int) -> str:
    return rid.sha256_bytes(rid.canonical_json(
        {"release_digest": release_digest, "arm": arm, "seed": int(seed),
         "study_id": STUDY_ID}))


def expected_run_plan() -> list[dict]:
    return [{"arm": arm, "seed": seed} for arm in APPROVED_ARMS for seed in APPROVED_SEEDS]


# --------------------------------------------------------------------------- #
# Phase A — structural validation
# --------------------------------------------------------------------------- #
def _require_mapping(value, code: str) -> dict:
    if not isinstance(value, dict):
        raise GateError(code)
    return value


def _check_release(expected_release_digest, release_report) -> str:
    if not isinstance(expected_release_digest, str) or not expected_release_digest:
        raise GateError("C1_RELEASE_DIGEST_MISMATCH")
    if release_report["release_digest"] != expected_release_digest:
        raise GateError("C1_RELEASE_DIGEST_MISMATCH")
    return release_report["release_digest"]


def _check_approval_structure(approval) -> dict:
    if approval is None:
        raise GateError("C1_AUTHORIZATION_REQUIRED")
    approval = _require_mapping(approval, "C1_AUTHORIZATION_REQUIRED")
    for field in REQUIRED_APPROVAL_FIELDS:
        value = approval.get(field)
        if not isinstance(value, str) or not value.strip():
            raise GateError("C1_AUTHORIZATION_INCOMPLETE")
    if approval["scope"] != STUDY_ID:
        # A BARR-M1 or any other scope is refused here.
        raise GateError("C1_AUTHORIZATION_SCOPE_MISMATCH")
    if approval["protocol_sha256"] != PROTOCOL_SHA256:
        raise GateError("C1_AUTHORIZATION_PROTOCOL_MISMATCH")
    if approval.get("arms") is None:
        raise GateError("C1_AUTHORIZATION_ARMS_MISMATCH")
    if set(approval.get("arms", [])) != set(APPROVED_ARMS) or \
            len(list(approval.get("arms", []))) != len(APPROVED_ARMS):
        raise GateError("C1_AUTHORIZATION_ARMS_MISMATCH")
    if list(approval.get("seeds", [])) != list(APPROVED_SEEDS):
        raise GateError("C1_AUTHORIZATION_SEEDS_MISMATCH")
    if not REQUIRED_EXCLUSIONS.issubset(set(approval.get("exclusions", []))):
        raise GateError("C1_AUTHORIZATION_EXCLUSIONS_MISSING")
    return approval


def _check_populations(protocol: dict, approval: dict) -> None:
    frozen = protocol["dataset"]["populations"]
    declared = approval.get("populations")
    if not isinstance(declared, dict) or set(declared) != set(frozen):
        raise GateError("C1_POPULATION_IDENTITY_MISMATCH")
    for split, expected in frozen.items():
        claimed = declared[split]
        if not isinstance(claimed, dict):
            raise GateError("C1_POPULATION_IDENTITY_MISMATCH")
        if claimed.get("path") != expected["path"]:
            raise GateError("C1_POPULATION_IDENTITY_MISMATCH")
        if claimed.get("n") != expected["n"]:
            raise GateError("C1_POPULATION_IDENTITY_MISMATCH")
        if claimed.get("sha256") != expected["sha256"]:
            raise GateError("C1_POPULATION_IDENTITY_MISMATCH")


def _check_prohibited_paths(protocol: dict, approval: dict) -> None:
    prohibited_tokens = ("test", "router_holdout", "router-holdout", "external", "quarantine")
    for split, info in protocol["dataset"]["populations"].items():
        if split not in ("TRAIN", "VAL"):
            raise GateError("C1_PROHIBITED_SPLIT")
        name = Path(info["path"]).name.lower()
        if any(token in name for token in prohibited_tokens):
            raise GateError("C1_PROHIBITED_SPLIT")
    for value in approval.get("requested_paths", []) or []:
        lowered = str(value).lower()
        if any(token in lowered for token in prohibited_tokens):
            raise GateError("C1_PROHIBITED_SPLIT")
    for split in approval.get("requested_splits", []) or []:
        if str(split).upper() not in ("TRAIN", "VAL"):
            raise GateError("C1_PROHIBITED_SPLIT")


def _check_budget(budget, run_plan) -> None:
    budget = _require_mapping(budget, "C1_BUDGET_EXCEEDED")
    if budget.get("logical_runs") != LOGICAL_RUNS:
        raise GateError("C1_BUDGET_EXCEEDED")
    epochs = budget.get("max_epochs")
    if not isinstance(epochs, int) or epochs <= 0 or epochs > MAX_EPOCHS:
        raise GateError("C1_BUDGET_EXCEEDED")
    hours = budget.get("max_cumulative_active_hours")
    if not isinstance(hours, (int, float)) or hours <= 0 or hours > MAX_CUMULATIVE_ACTIVE_HOURS:
        raise GateError("C1_BUDGET_EXCEEDED")
    plan = list(run_plan or [])
    keys = [(entry.get("arm"), entry.get("seed")) for entry in plan
            if isinstance(entry, dict)]
    if len(keys) != len(plan) or len(set(keys)) != len(keys):
        raise GateError("C1_DUPLICATE_LOGICAL_RUN")
    if set(keys) != {(a, s) for a in APPROVED_ARMS for s in APPROVED_SEEDS}:
        raise GateError("C1_BUDGET_EXCEEDED")


def _check_recovery(recovery, release_digest: str, output_root: Path) -> None:
    recovery = _require_mapping(recovery, "C1_RECOVERY_IDENTITY_INVALID")
    mode = recovery.get("mode")
    if mode not in ("FRESH", "RESUME"):
        raise GateError("C1_RECOVERY_IDENTITY_INVALID")
    arm, seed = recovery.get("arm"), recovery.get("seed")
    if arm not in APPROVED_ARMS or seed not in APPROVED_SEEDS:
        raise GateError("C1_RECOVERY_IDENTITY_INVALID")
    expected = run_identity(release_digest, arm, seed)
    if mode == "RESUME":
        if recovery.get("identity") != expected:
            raise GateError("C1_RECOVERY_IDENTITY_INVALID")
    else:
        if recovery.get("identity") not in (None, expected):
            raise GateError("C1_RECOVERY_IDENTITY_INVALID")
        attempt = Path(output_root) / f"seed{seed}" / arm
        if (attempt / "latest.json").exists() or (attempt / "lifecycle.json").exists():
            raise GateError("C1_RECOVERY_IDENTITY_INVALID")


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not _ISO.match(value):
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _check_trusted_time(attestation, now: datetime) -> None:
    attestation = _require_mapping(attestation, "C1_TRUSTED_TIME_UNVERIFIED")
    if attestation.get("synchronized") is not True:
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED")
    if attestation.get("source") not in TRUSTED_TIME_SOURCES:
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED")
    offset = attestation.get("abs_offset_seconds")
    if not isinstance(offset, (int, float)) or offset < 0:
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED")
    if float(offset) > MAX_TRUSTED_TIME_OFFSET_SECONDS:
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED")
    measured = _parse_utc(attestation.get("measured_at_utc"))
    age = now - measured
    if age < timedelta(0) or age > timedelta(hours=MAX_TRUSTED_TIME_AGE_HOURS):
        raise GateError("C1_TRUSTED_TIME_UNVERIFIED")


def _check_launch_instruction(instruction, approval: dict, release_digest: str,
                              run_plan, now: datetime) -> None:
    if instruction is None:
        raise GateError("C1_SEPARATE_LAUNCH_REQUIRED")
    instruction = _require_mapping(instruction, "C1_SEPARATE_LAUNCH_REQUIRED")
    for field in ("launch_id", "authorization_id", "release_digest", "issued_at"):
        if not isinstance(instruction.get(field), str) or not instruction[field].strip():
            raise GateError("C1_LAUNCH_INSTRUCTION_INCOMPLETE")
    if instruction["authorization_id"] != approval["authorization_id"]:
        raise GateError("C1_LAUNCH_INSTRUCTION_MISMATCH")
    if instruction["launch_id"] == approval["authorization_id"]:
        # The launch instruction must be a distinct artifact, not a copy.
        raise GateError("C1_SEPARATE_LAUNCH_REQUIRED")
    if instruction["release_digest"] != release_digest:
        raise GateError("C1_LAUNCH_INSTRUCTION_MISMATCH")
    approved_at = _parse_utc(approval["authorized_at"])
    issued_at = _parse_utc(instruction["issued_at"])
    if issued_at < approved_at:
        raise GateError("C1_LAUNCH_ORDER_VIOLATION")
    if issued_at - now > timedelta(hours=MAX_TRUSTED_TIME_AGE_HOURS):
        raise GateError("C1_LAUNCH_ORDER_VIOLATION")
    plan = instruction.get("run_plan")
    if not isinstance(plan, list):
        raise GateError("C1_LAUNCH_INSTRUCTION_MISMATCH")
    keys = [(e.get("arm"), e.get("seed")) for e in plan if isinstance(e, dict)]
    if len(keys) != len(plan) or set(keys) != {(a, s) for a in APPROVED_ARMS for s in APPROVED_SEEDS}:
        raise GateError("C1_LAUNCH_INSTRUCTION_MISMATCH")
    if run_plan is not None and plan != list(run_plan):
        raise GateError("C1_LAUNCH_INSTRUCTION_MISMATCH")


# --------------------------------------------------------------------------- #
# Phase B — trust establishment
# --------------------------------------------------------------------------- #
def _establish_trust(anchor_path, approval: dict, instruction: dict) -> dict:
    anchor = load_trust_anchor(anchor_path)
    fingerprint = anchor_fingerprint(anchor["public_key_pem"])
    if fingerprint not in AUTHORIZED_ANCHOR_SHA256:
        raise GateError("C1_TRUST_ANCHOR_NOT_ALLOWLISTED")
    if approval.get("authorized_by") != anchor["institution"]:
        raise GateError("C1_AUTHORIZATION_SOURCE_MISMATCH")
    if approval.get("institutional_role") not in anchor["authorized_roles"]:
        raise GateError("C1_AUTHORIZATION_ROLE_MISMATCH")
    for signature, payload, code in (
        (approval.get("signature"), approval, "C1_APPROVAL_SIGNATURE_INVALID"),
        (instruction.get("signature"), instruction, "C1_LAUNCH_SIGNATURE_INVALID"),
    ):
        if not isinstance(signature, str) or not signature.strip():
            raise GateError(code)
        if not verify_detached_signature(anchor["public_key_pem"], payload, signature):
            raise GateError(code)
    return anchor


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def assert_launch_authorized(*, expected_release_digest, approval=None, instruction=None,
                             anchor_path=None, budget=None, run_plan=None, recovery=None,
                             trusted_time=None, output_root=None, now=None) -> dict:
    """Run the full chain. Returns a verification record; raises GateError on refusal.

    Never returns without a Phase-B allowlisted anchor, which this release does
    not provide.
    """
    now = now or datetime.now(timezone.utc)
    output_root = Path(output_root) if output_root is not None else (
        rid.ROOT / "experiments/c1_film_attribution_v1")

    try:
        release = rid.verify_release()
    except rid.ReleaseIdentityError as exc:
        raise GateError(str(exc)) from exc
    release_digest = _check_release(expected_release_digest, release)

    protocol = json.loads(rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    if protocol.get("study_id") != STUDY_ID:
        raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")
    if protocol.get("execution", {}).get("separate_launch_required") is not True:
        raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")

    approval = _check_approval_structure(approval)
    if approval["release_digest"] != release_digest:
        raise GateError("C1_AUTHORIZATION_RELEASE_MISMATCH")
    _check_populations(protocol, approval)
    _check_prohibited_paths(protocol, approval)
    _check_budget(budget, run_plan)
    _check_recovery(recovery, release_digest, output_root)
    _check_trusted_time(trusted_time, now)
    _check_launch_instruction(instruction, approval, release_digest, run_plan, now)

    anchor = _establish_trust(anchor_path, approval, instruction)

    return {
        "study_id": STUDY_ID,
        "release_digest": release_digest,
        "authorization_id": approval["authorization_id"],
        "launch_id": instruction["launch_id"],
        "anchor_fingerprint": anchor_fingerprint(anchor["public_key_pem"]),
        "run_plan": list(run_plan),
        "authorized_at": approval["authorized_at"],
        "issued_at": instruction["issued_at"],
    }


class LaunchGrant:
    """Opaque capability. Constructible only through ``assert_launch_authorized``."""

    __slots__ = ("_record",)
    _MINT = object()

    def __init__(self, record: dict, *, token=None):
        if token is not LaunchGrant._MINT:
            raise GateError("C1_LAUNCH_GRANT_FORGED")
        self._record = dict(record)

    # -- accessors ---------------------------------------------------------
    @property
    def release_digest(self) -> str:
        return self._record["release_digest"]

    @property
    def record(self) -> dict:
        return dict(self._record)

    # -- re-verification on every use -------------------------------------
    def _reverify(self) -> str:
        try:
            release = rid.verify_release()
        except rid.ReleaseIdentityError as exc:
            raise GateError(str(exc)) from exc
        if release["release_digest"] != self._record["release_digest"]:
            raise GateError("C1_RELEASE_DIGEST_STALE")
        return release["release_digest"]

    def authorize_trainer(self, contract: dict) -> None:
        self._reverify()
        if contract.get("study_id") != STUDY_ID:
            raise GateError("C1_CONTRACT_SCOPE_MISMATCH")
        if contract.get("protocol_sha256") != PROTOCOL_SHA256:
            raise GateError("C1_AUTHORIZATION_PROTOCOL_MISMATCH")
        pair = (contract.get("arm"), contract.get("seed"))
        if pair not in {(e["arm"], e["seed"]) for e in self._record["run_plan"]}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")

    def authorize_loader(self, protocol: dict) -> None:
        self._reverify()
        if protocol.get("study_id") != STUDY_ID:
            raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")
        if set(protocol["dataset"]["populations"]) != {"TRAIN", "VAL"}:
            raise GateError("C1_PROHIBITED_SPLIT")

    def authorize_launch(self, protocol: dict, arm: str, seed: int) -> None:
        self.authorize_loader(protocol)
        pair = (arm, seed)
        if pair not in {(e["arm"], e["seed"]) for e in self._record["run_plan"]}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")


def mint_grant(**kwargs) -> LaunchGrant:
    record = assert_launch_authorized(**kwargs)
    return LaunchGrant(record, token=LaunchGrant._MINT)
