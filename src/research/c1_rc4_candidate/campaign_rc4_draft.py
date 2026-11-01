"""DRAFT RC4 campaign orchestration. NOT a sealed, published or authorized release.

This module is not bound by any release manifest. It exists so a separately reviewed
release can bind it. Real training is refused unconditionally while
``DRAFT_AUTHORIZED`` is False; only preflight (no data access, no training) works.

Differences from ``scripts/analysis/run_c1_campaign_launch.py`` (RC3, untouched):
  * RC4 gate/driver only; RC1-RC3 release digests are refused up front.
  * The legacy trust store is never loaded (RC4 trust loader refuses it).
  * One distinct, signed, single-use time proof and one recovery record per run.
  * The institutional owner-key fingerprint must be supplied out of band by the
    caller (not read from the repository, the trust store, or the artifacts) and is
    compared with the key that signed the trust policy.
  * Scientific recipe, populations and run plan are the frozen ones, unchanged.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from src.research.c1_film_launch import launch_gate as rc1
from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc2.trust_policy import spki_fingerprint
from src.research.c1_film_launch_rc4 import launch_driver_rc4, rc4_gate, trust_rc4
from src.research.c1_film_launch_rc4 import release_identity_rc4 as rid

DRAFT_AUTHORIZED = False
_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


def run_key(arm: str, seed: int) -> str:
    return f"{arm}_seed{seed}"


def frozen_run_plan() -> list:
    plan = rc1.expected_run_plan()
    expected = {(a, s) for a in ("C1-T", "C1-C") for s in (42, 123, 3407)}
    if len(plan) != 6 or {(e["arm"], e["seed"]) for e in plan} != expected:
        raise GateError("C1_RC4_DRAFT_RUN_PLAN_DRIFT")
    return plan


def normalize_fingerprint(value) -> str:
    text = str(value or "").strip().lower().replace(":", "")
    if not _FINGERPRINT.match(text):
        raise GateError("C1_RC4_EXTERNAL_ANCHOR_REQUIRED")
    return text


def verify_external_anchor(binding: dict, expected_fingerprint) -> None:
    """The policy-owner key must match a fingerprint authenticated outside this workspace."""
    expected = normalize_fingerprint(expected_fingerprint)
    actual = str(spki_fingerprint(binding["policy_owner_public_key_pem"])).lower().replace(":", "")
    if actual != expected:
        raise GateError("C1_RC4_EXTERNAL_ANCHOR_MISMATCH")


def _refuse_predecessor(expected_release_digest) -> None:
    if expected_release_digest in rid.PREDECESSOR_DIGESTS:
        raise GateError("C1_RC4_PREDECESSOR_IDENTITY_REJECTED")


def _load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def preflight_run(arm: str, seed: int, *, expected_release_digest: str,
                  owner_key_fingerprint: str, artifacts: dict, trust_store_root=None,
                  require_owner: bool = True, output_root=None, now=None,
                  consume_nonce: bool = False) -> dict:
    """Full RC4 authorization for one run. Touches no dataset and starts no training."""
    _refuse_predecessor(expected_release_digest)
    plan = frozen_run_plan()
    if (arm, seed) not in {(e["arm"], e["seed"]) for e in plan}:
        raise GateError("C1_RUN_NOT_AUTHORIZED")
    root = Path(trust_store_root) if trust_store_root is not None else trust_rc4.PRODUCTION_ROOT
    binding, _ = trust_rc4.load_trust_store_rc4(root, require_owner=require_owner)
    verify_external_anchor(binding, owner_key_fingerprint)
    key = run_key(arm, seed)
    recovery = artifacts["recovery"][key]
    if (recovery.get("arm"), recovery.get("seed")) != (arm, seed):
        raise GateError("C1_RECOVERY_IDENTITY_INVALID")
    return rc4_gate.validate_authorization(
        expected_release_digest=expected_release_digest, approval=artifacts["approval"],
        instruction=artifacts["instruction"], time_status=artifacts["time_status"][key],
        budget=artifacts["budget"], run_plan=plan, recovery=recovery,
        output_root=output_root, now=now or datetime.now(timezone.utc),
        trust_store_root=root, require_owner=require_owner, consume_nonce=consume_nonce)


def load_artifacts(*, approval, instruction, budget, time_proof_dir, recovery_dir) -> dict:
    out = {"approval": _load(approval), "instruction": _load(instruction),
           "budget": _load(budget), "time_status": {}, "recovery": {}}
    for item in frozen_run_plan():
        key = run_key(item["arm"], item["seed"])
        for name, folder in (("time_status", time_proof_dir), ("recovery", recovery_dir)):
            path = Path(folder) / f"{key}.json"
            if not path.is_file():
                raise FileNotFoundError(f"Missing per-run {name} artifact: {path}")
            out[name][key] = _load(path)
    nonces = [p.get("nonce") for p in out["time_status"].values()]
    if len(set(nonces)) != len(nonces):
        raise GateError("C1_RC4_TIME_PROOF_NOT_DISTINCT")
    return out


def execute_campaign(*, expected_release_digest: str, owner_key_fingerprint: str,
                     artifacts: dict, trust_store_root=None, output_root=None,
                     execute: bool = False, launch_fn: Optional[Callable] = None,
                     require_owner: bool = True) -> list:
    """Preflight all six runs; real execution is refused for this draft."""
    if execute and not DRAFT_AUTHORIZED:
        raise GateError("C1_RC4_DRAFT_LAUNCHER_NOT_AUTHORIZED")
    records = []
    for item in frozen_run_plan():
        arm, seed = item["arm"], item["seed"]
        records.append(preflight_run(
            arm, seed, expected_release_digest=expected_release_digest,
            owner_key_fingerprint=owner_key_fingerprint, artifacts=artifacts,
            trust_store_root=trust_store_root, require_owner=require_owner,
            output_root=output_root, consume_nonce=False))
    return records
