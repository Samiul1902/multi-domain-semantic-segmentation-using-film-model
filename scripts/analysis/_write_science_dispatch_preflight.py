import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = r"D:\Softfors\jup"


def raw(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


out = os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_dispatch_preflight_v1.json")
if os.path.exists(out):
    print("EXISTS already, refusing:", out)
    raise SystemExit(0)

payload = {
    "artifact": "phase36_v1_14_science_dispatch_preflight",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "SCIENCE_DISPATCH_PREFLIGHT_FORENSIC_SNAPSHOT",
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "pins": {
        "execution_source_sha256": raw(os.path.join(ROOT, "scripts", "analysis", "phase36_robustness_execution_v1_14.py")),
        "launcher_sha256": raw(os.path.join(ROOT, "scripts", "analysis", "launch_phase36_v1_14.py")),
        "runtime_manifest_sha256": raw(os.path.join(ROOT, "reports", "audits", "phase36_v1_14_runtime_source_integrity_manifest.json")),
        "smoke_result_sha256": raw(os.path.join(ROOT, "reports", "audits", "phase36_robustness_smoke_v1_14.json")),
        "science_release_attestation_sha256": raw(os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_release_attestation.json")),
    },
    "marker_absent": not os.path.exists(os.path.join(ROOT, "reports", "audits", "phase36_robustness_science_start_v1_14.json")),
    "wrapped_start_process_failure": {
        "mechanism": "PowerShell Start-Process (work-order mandated)",
        "error": "Item has already been added. Key in dictionary: 'PATH'  Key being added: 'Path'",
        "layer": "PowerShell/.NET process-launch environment block",
        "python_invoked": False,
        "main_entered": False,
        "revision_consumed": False,
        "stdout_log_sha256": raw(os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_stdout_first_attempt.txt")),
        "stderr_log_sha256": raw(os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_stderr_first_attempt.txt")),
    },
    "redundant_corrected_dispatch": "clean cmd /c invocation of canonical venv interpreter; identical authorized command/interpreter/args/env",
    "revision_unconsumed_at_snapshot": True,
}

flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
fd = os.open(out, flags, 0o644)
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
except BaseException:
    os.close(fd)
    raise
print("WROTE", out, raw(out))
