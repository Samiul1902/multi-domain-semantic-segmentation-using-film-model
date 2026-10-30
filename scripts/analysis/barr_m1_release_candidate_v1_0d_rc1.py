"""BARR-M1 RC1: inactive until independent machine trust, approval AND launch.

No trust installer, private key generator, synthetic flag, or clock override.
Run with Python -I: the frozen entrypoint pins its local runtime dependencies.
"""
import argparse
import base64
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import importlib.metadata
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts/analysis/barr_m1_v1_0d_repaired"
PINNED = {
    "analysis.py": "1e778cd5f9a44075a65e5702703b471aa9f75974f698e0af3611b793a5daf0d2",
    "authorization.py": "d85975c0c020f791ae9fc6c516a3251821a2bebb929617858070b4611edf995b",
    "contracts.py": "0257eb71f66a73a933a0ebdf086801c05977bc1afd05eee728bcb85fbf52f5cf",
    "storage.py": "8ff6d536ab6aa99b7b333db2962373f2138b51cf1c90c8d52230a30f9cab583b",
    "__init__.py": "ae26a7a4e44634aa836da4073befd3b5c4593cdbff8dd77ef77ac6f06712fb5d",
    "__main__.py": "ebe41f5013ed78dbc4149b91ef8e2c1a5a84f6b1b8dfe1dccf779478c69b538a",
    "requirements.txt": "5b67f202126e0492b824fcb17c6b54b726ef95bc9eb2cad1403757a0e14aa7c8",
}
TRUST_REGISTRY = r"SOFTWARE\RA-MedFiLM-BARR\BARR-M1"
OUTPUT_RELATIVE = "reports/scientific/barr_m1_v1_0d_rc1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_runtime():
    for name, expected in PINNED.items():
        if sha((PACKAGE / name).read_bytes()) != expected:
            raise RuntimeError("E_RUNTIME_SHA_MISMATCH: " + name)
    for name, expected in {"cryptography": "50.0.2", "numpy": "2.4.6", "pandas": "3.0.5"}.items():
        if importlib.metadata.version(name) != expected:
            raise RuntimeError("E_RUNTIME_VERSION: " + name)


verify_runtime()
# Load the verified package under a private name without executing repository
# parent __init__ files or trusting PYTHONPATH. Deployment requires Python -I.
spec = importlib.util.spec_from_file_location("_barr_rc1_frozen", PACKAGE / "__init__.py",
                                            submodule_search_locations=[str(PACKAGE)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
from _barr_rc1_frozen import contracts as c, authorization as auth, analysis as analysis, storage as storage
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def executable_sha():
    return sha(Path(__file__).read_bytes())


def parse_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            c.require(key not in result, "E_JSON_DUPLICATE_KEY")
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    except (TypeError, ValueError) as exc:
        raise c.Refusal("E_JSON_INVALID", str(exc)) from exc


def read_request(path):
    c.require(path is not None, "E_AUTHORIZATION_UNSIGNED")
    path = Path(path)
    c.require(path.suffix.lower() == ".json" and not path.is_symlink(), "E_REQUEST_PATH")
    c.require(not any(x in str(path).lower() for x in ("router_holdout", "external", "test.csv", "checkpoints")), "E_PATH_PROTECTED")
    c.require(path.stat().st_size <= 65536, "E_REQUEST_SIZE")
    return parse_json(path.read_bytes())


def validate_registry_acl(record):
    """Only SYSTEM/Administrators may own or write independent trust policy."""
    privileged = {"S-1-5-18", "S-1-5-32-544"}
    c.require(record.get("owner") in privileged, "E_TRUST_ACL")
    c.require(isinstance(record.get("rules"), list) and bool(record["rules"]), "E_TRUST_ACL")
    write_bits = 2 | 4 | 32 | 65536 | 262144 | 524288
    for rule in record["rules"]:
        c.require(not (rule["allow"] and int(rule["rights"]) & write_bits and
                       rule["sid"] not in privileged), "E_TRUST_ACL")


def machine_policy():
    """Read-only HKLM integration. Nothing is provisioned by this executable."""
    c.require(os.name == "nt" and ctypes.sizeof(ctypes.c_void_p) == 8,
              "E_AUTHORIZATION_TRUST_ANCHOR_ABSENT", "requires independent 64-bit Windows machine policy")
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, TRUST_REGISTRY, 0,
                           winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            raw, kind = winreg.QueryValueEx(key, "Policy")
        c.require(kind == winreg.REG_SZ and len(raw) <= 65536, "E_TRUST_POLICY")
        # Fixed executable and script; no payload-controlled PowerShell commands.
        windir = ctypes.create_unicode_buffer(32768)
        c.require(ctypes.windll.kernel32.GetWindowsDirectoryW(windir, len(windir)) > 0, "E_TRUST_ACL")
        shell = Path(windir.value) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        script = r"""
$ErrorActionPreference='Stop'
$paths=@('Registry::HKEY_LOCAL_MACHINE\SOFTWARE\RA-MedFiLM-BARR', 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\RA-MedFiLM-BARR\BARR-M1')
$result=@(foreach($p in $paths) {
 $acl=Get-Acl -LiteralPath $p
 $owner=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
 $rules=@($acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier]) | ForEach-Object {
  @{sid=$_.IdentityReference.Value;rights=[int]$_.RegistryRights;allow=($_.AccessControlType -eq 'Allow')}
 })
 @{owner=$owner;rules=$rules}
})
ConvertTo-Json -InputObject $result -Depth 8 -Compress
"""
        completed = subprocess.run([str(shell), "-NoProfile", "-NonInteractive", "-Command", script],
            check=True, capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        records = parse_json(completed.stdout)
        c.require(isinstance(records, list) and len(records) == 2, "E_TRUST_ACL")
        for record in records:
            validate_registry_acl(record)
        return validate_policy(parse_json(raw))
    except (OSError, subprocess.SubprocessError) as exc:
        raise c.Refusal("E_AUTHORIZATION_TRUST_ANCHOR_ABSENT", "independent policy unavailable") from exc


def validate_policy(policy):
    fields = {"environment", "keys", "revoked_authorization_ids", "revoked_key_ids", "time_public_key", "time_key_sha256", "time_url"}
    c.require(isinstance(policy, dict) and set(policy) == fields and policy["environment"] == "PRODUCTION", "E_TRUST_POLICY")
    c.require(isinstance(policy["keys"], dict) and bool(policy["keys"]), "E_AUTHORIZATION_TRUST_ANCHOR_ABSENT")
    for value in policy["keys"].values():
        c.require(set(value) == {"public_key", "fingerprint_sha256", "approver"} and
                  isinstance(value["approver"], str) and bool(value["approver"].strip()), "E_TRUST_POLICY")
        key_bytes(value["public_key"], value["fingerprint_sha256"])
    key_bytes(policy["time_public_key"], policy["time_key_sha256"])
    url = urllib.parse.urlsplit(policy["time_url"])
    c.require(url.scheme == "https" and bool(url.hostname) and not url.username and not url.password and not url.fragment,
              "E_TRUST_POLICY")
    for name in ("revoked_authorization_ids", "revoked_key_ids"):
        c.require(isinstance(policy[name], list) and all(isinstance(x, str) for x in policy[name]), "E_TRUST_POLICY")
    return policy


def key_bytes(encoded, fingerprint):
    try:
        raw = base64.b64decode(encoded, validate=True)
        c.require(len(raw) == 32 and sha(raw) == fingerprint, "E_TRUST_FINGERPRINT")
        return raw
    except (ValueError, TypeError) as exc:
        raise c.Refusal("E_TRUST_FINGERPRINT") from exc


def signed_payload(envelope, public_key):
    c.require(isinstance(envelope, dict) and set(envelope) == {"payload", "signature"}, "E_AUTHORIZATION_UNSIGNED")
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            base64.b64decode(envelope["signature"], validate=True), c.canonical(envelope["payload"]))
    except (InvalidSignature, ValueError, TypeError):
        raise c.Refusal("E_AUTHORIZATION_SIGNATURE_INVALID") from None
    return envelope["payload"]


def utc(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        c.require(parsed.tzinfo is not None, "E_TRUSTED_TIME")
        return parsed.astimezone(timezone.utc)
    except (AttributeError, TypeError, ValueError):
        raise c.Refusal("E_TRUSTED_TIME") from None


def check_time_response(envelope, policy, challenge, elapsed):
    c.require(0 <= elapsed <= 10, "E_TRUSTED_TIME", "freshness round trip exceeded")
    payload = signed_payload(envelope, key_bytes(policy["time_public_key"], policy["time_key_sha256"]))
    c.require(isinstance(payload, dict) and set(payload) == set(challenge) | {"utc", "authorization_and_launch_active"}, "E_TRUSTED_TIME")
    c.require(all(payload[k] == v for k, v in challenge.items()) and
              payload["authorization_and_launch_active"] is True, "E_TRUSTED_TIME", "nonce/context mismatch or revoked")
    return utc(payload["utc"])


def trusted_time(policy, approval, launch):
    """Fresh signed nonce response; never validates approvals against host UTC."""
    challenge = dict(nonce=secrets.token_hex(32), authorization_sha256=sha(c.canonical(approval)),
                     launch_sha256=sha(c.canonical(launch)))
    request = urllib.request.Request(policy["time_url"], c.canonical(challenge), {"Content-Type": "application/json"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise c.Refusal("E_TRUSTED_TIME", "redirect refused")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    start = time.monotonic()
    try:
        with opener.open(request, timeout=10) as response:
            body = response.read(65537)
        c.require(len(body) <= 65536, "E_TRUSTED_TIME")
        return check_time_response(parse_json(body), policy, challenge, time.monotonic()-start)
    except (OSError, ValueError) as exc:
        raise c.Refusal("E_TRUSTED_TIME", "independent signed time/revocation service unavailable") from exc


def verify_requests(approval, launch, policy, now, harness_sha):
    """Shared production verifier; tests inject policy/time only into this pure layer."""
    validate_policy(policy)
    c.require(isinstance(now, datetime) and now.tzinfo is not None, "E_TRUSTED_TIME")
    keys = {kid: dict(public_key=key_bytes(v["public_key"], v["fingerprint_sha256"]), approver=v["approver"])
            for kid, v in policy["keys"].items()}
    approved = auth.verify_envelope(approval, keys, harness_sha, now=now,
        revoked_ids=set(policy["revoked_authorization_ids"]), revoked_keys=set(policy["revoked_key_ids"]))
    c.require(isinstance(launch, dict) and set(launch) == {"key_id", "payload", "signature"}, "E_LAUNCH_REQUIRED")
    kid = launch["key_id"]
    c.require(isinstance(kid, str) and kid in keys and kid not in policy["revoked_key_ids"], "E_AUTHORIZATION_SIGNATURE_INVALID")
    payload = signed_payload({k: launch[k] for k in ("payload", "signature")}, keys[kid]["public_key"])
    expected = dict(purpose="SEPARATE_EXPLICIT_LAUNCH_WORK_ORDER", study_identifier="BARR-M1",
        authorization_id=approved["authorization_id"], authorization_sha256=sha(c.canonical(approval)),
        harness_sha256=harness_sha, output_relative=OUTPUT_RELATIVE, execution_mode="CPU_ONLY_RE_ANALYSIS_ONLY")
    c.require(isinstance(payload, dict) and set(payload) == set(expected) | {"work_order_id", "issued_by", "issued_at", "expires_at"}, "E_LAUNCH_SCOPE")
    c.require(all(payload[k] == v for k, v in expected.items()) and payload["issued_by"] == keys[kid]["approver"]
              and isinstance(payload["work_order_id"], str) and bool(payload["work_order_id"].strip()), "E_LAUNCH_SCOPE")
    c.require(utc(approved["approval_date"]) <= utc(payload["issued_at"]) <= now < utc(payload["expires_at"]), "E_LAUNCH_EXPIRED")
    return approved


def verify_protocol():
    for relative, expected in {
        "reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_supervisor_authorization_request.md": c.PROTOCOL_SHA,
        "reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_erratum.md": c.ERRATUM_SHA,
    }.items():
        c.require(sha((ROOT / relative).read_bytes()) == expected, "E_PROTOCOL_SHA")


def load_sources():
    """Called only after approval + independent time + separate launch verify."""
    blobs = {}
    allowed = {p for p, _ in c.SOURCES.values()}
    for name, (relative, expected) in c.SOURCES.items():
        path = analysis.checked_path(ROOT, relative, allowed)
        data = path.read_bytes()
        c.require(sha(data) == expected, "E_INPUT_SHA_MISMATCH", name)
        blobs[name] = data
    # Every SHA passes before any scientific CSV is parsed or computed.
    return {name: analysis.pd.read_csv(io.BytesIO(data), dtype={"sample_id": str, "patient_id": str})
            for name, data in blobs.items()}


def output_root():
    return ROOT / OUTPUT_RELATIVE


def run_authorized(approval, launch, *, recover=False):
    c.validate_config(c.CONFIG)
    c.require(isinstance(approval, dict) and bool(approval.get("signature")), "E_AUTHORIZATION_UNSIGNED")
    c.require(isinstance(launch, dict) and bool(launch.get("signature")), "E_LAUNCH_REQUIRED")
    verify_runtime()
    policy = machine_policy()  # no caller-supplied production policy accepted
    now = trusted_time(policy, approval, launch)
    approved = verify_requests(approval, launch, policy, now, executable_sha())
    verify_protocol()
    frames = load_sources()
    # Recheck live validity/revocation immediately before computation.
    policy = machine_policy()
    now = trusted_time(policy, approval, launch)
    verify_requests(approval, launch, policy, now, executable_sha())
    result = analysis.analyze_frames(frames)
    result["authorization_sha256"] = sha(c.canonical(approval))
    result["launch_sha256"] = sha(c.canonical(launch))
    result["work_order_id"] = launch["payload"]["work_order_id"]
    binding = dict(input_shas=c.INPUT_SHAS, checkpoint_shas=c.CHECKPOINT_SHAS,
                   authorization_id=approved["authorization_id"], harness_sha256=executable_sha())
    return storage.commit(output_root(), binding, result, recover=recover)


def main(argv=None):
    parser = argparse.ArgumentParser(description="BARR-M1 RC1: independent approval and separate launch required")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--launch-work-order")
    parser.add_argument("--recover-partial", action="store_true")
    args = parser.parse_args(argv)
    try:
        c.validate_config(c.CONFIG)
        if not args.execute:
            print("NO_EXECUTION: release candidate inactive; approval and separate launch required")
            return 0
        c.require(sys.flags.isolated == 1, "E_ISOLATED_INTERPRETER_REQUIRED", "use the pinned environment with Python -I")
        c.require(args.authorization and args.launch_work_order, "E_AUTHORIZATION_UNSIGNED", "approval and separate launch records required")
        result = run_authorized(read_request(args.authorization), read_request(args.launch_work_order), recover=args.recover_partial)
        print(str(result))
        return 0
    except (c.Refusal, OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print("REFUSED: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
