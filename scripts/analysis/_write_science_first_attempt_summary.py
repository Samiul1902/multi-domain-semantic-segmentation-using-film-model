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


out = os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_first_attempt_summary.json")
if os.path.exists(out):
    print("EXISTS, refusing:", out)
    raise SystemExit(0)

start = os.path.join(ROOT, "reports", "audits", "phase36_robustness_science_start_v1_14.json")
fail = os.path.join(ROOT, "reports", "audits", "phase36_robustness_science_failure_v1_14.json")
so = os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_stdout_first_attempt.txt")
se = os.path.join(ROOT, "reports", "audits", "phase36_v1_14_science_stderr_first_attempt.txt")
res = os.path.join(ROOT, "reports", "audits", "phase36_robustness_scientific_result_v1_14.json")

payload = {
    "artifact": "phase36_v1_14_science_first_attempt_summary",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "SCIENCE_FIRST_ATTEMPT_SUMMARY",
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "result": "FAILURE",
    "exit_code": 1,
    "science_start_marker_sha256": raw(start),
    "science_failure_artifact_sha256": raw(fail),
    "science_result_present": os.path.exists(res),
    "stdout_log_sha256": raw(so),
    "stderr_log_sha256": raw(se),
    "stdout_bytes": os.path.getsize(so),
    "stderr_bytes": os.path.getsize(se),
    "failure_terminal": "PHASE36_V1_14_SCIENCE_FIRST_ATTEMPT_FAILED__ARTIFACT_PRESERVED__NO_RETRY",
    "failure_message": "CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION",
    "failure_termination_kind": "SYSTEM_EXIT",
    "failure_is_crash": False,
    "stopped_before_perturbation": True,
    "scientific_output": False,
    "science_retry_performed": False,
    "smoke_retry_performed": False,
    "phase37_state": "NOT_STARTED",
    "test_state": "REMAINS_PHASE39_ONLY",
    "router_holdout_state": "NOT_ACCESSED",
    "pinned_execution_source_sha256": raw(os.path.join(ROOT, "scripts", "analysis", "phase36_robustness_execution_v1_14.py")),
    "pinned_launcher_sha256": raw(os.path.join(ROOT, "scripts", "analysis", "launch_phase36_v1_14.py")),
    "note": ("First and only v1.14 science attempt. Revision CONSUMED. No repair, no retry, "
             "no source modification. Evidence preserved verbatim for independent audit."),
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
