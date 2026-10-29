# External Operator Action Checklist — C1 Production Launch (RC3)

**Authority Requirement:** Must be executed by a human institutional operator / supervisor.  
**Strict Prohibition:** Never fabricate signatures, time attestations, or hardware clock proofs.  
**Updated for:** RC3 (host-clock path now implementable without further release)

---

## Step 1 — Windows Hardware Clock & NTP Synchronization

### 1a. Verify hardware (CMOS) clock
Ensure the CMOS battery is functional and RTC retains time across power cycles.

### 1b. Synchronize Windows Time Service (admin PowerShell)
```powershell
w32tm /resync /force
w32tm /query /status
```
Record the output. The `Last Successful Sync Time` field must be within the last 5 minutes.

### 1c. Measure NTP offset from Python (RC3 tool — requires network)
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" -c "
from src.research.c1_film_launch_rc3.time_status_rc3 import measure_ntp_offset
import json
result = measure_ntp_offset()
print(json.dumps(result, indent=2))
"
```
**Required:** `|offset_seconds|` < 1.0 second. Record the exact value.  
If offset > 1.0 s, stop. Do not proceed until clock is corrected.

---

## Step 2 — Provision OS-Scope Trust Store

Create the production trust store directory with restricted ACLs:
```powershell
New-Item -ItemType Directory -Path "C:\ProgramData\InstitutionalC1Trust" -Force
icacls "C:\ProgramData\InstitutionalC1Trust" /inheritance:r /grant:r "$($env:USERNAME):(OI)(CI)F"
```

Generate ECDSA-P256 keypairs for three roles:
- `TIME_AUTHORITY` — signs clock attestations
- `SUPERVISOR` (APPROVAL role) — signs scientific approval
- `LAUNCH_OPERATOR` — signs launch instruction

Build and sign the trust policy JSON (`c1_rc2_binding.json` + policy file) using your institutional key management process.  
**Do not generate keys inside the repository.**

---

## Step 3 — Write Signed Host Clock Attestation (RC3)

With the NTP measurement result from Step 1c and the TIME_AUTHORITY private key:
```python
from src.research.c1_film_launch_rc3.time_status_rc3 import (
    measure_ntp_offset, write_host_clock_attestation
)
# Load your TIME_AUTHORITY private key securely (not from repo)
# private_key = load_from_hsm_or_keystore(...)

ntp_result = measure_ntp_offset()
attestation = write_host_clock_attestation(
    private_key=private_key,
    key_id="<your-time-authority-key-id>",
    ntp_result=ntp_result,
    trust_store_root=r"C:\ProgramData\InstitutionalC1Trust",
    tolerance_seconds=1.0,
)
print("Clock trust attestation written. Verdict:", attestation["verdict"])
print("NTP offset:", attestation["offset_seconds"], "s")
```
The attestation is valid for 24 hours. Re-run before each launch session if expired.

---

## Step 4 — Issue Signed Scientific Approval

The institutional SUPERVISOR signs an approval record binding:
- `study_id`: `C1_FILM_ATTRIBUTION_V1`
- `protocol_sha256`: `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61`
- `release_digest` (RC2): `54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed`
- `arms`: `["C1-T", "C1-C"]`
- `seeds`: `[42, 123, 3407]`
- `exclusions`: `["TEST", "ROUTER_HOLDOUT", "EXTERNAL", "QUARANTINE", "BARR-M1", "C2", "C3"]`
- `authorization_id`: unique string (UUID recommended)
- `authorized_by`: institutional role and name
- `authorized_at`: ISO 8601 UTC timestamp

Signed with SUPERVISOR/INSTITUTIONAL_APPROVER role key from the trust store.

---

## Step 5 — Issue Separate Signed Launch Instruction

The LAUNCH_OPERATOR signs a launch instruction binding:
- `authorization_id` from Step 4
- `run_plan`: exactly 6 entries (arm, seed pairs)
- `launch_id`: unique string
- Timestamp

Signed with LAUNCH_OPERATOR role key.

---

## Step 6 — Configure Private GitHub Remote

Verify no sensitive credentials appear in tracked files:
```powershell
git -C D:\Softfors\jup log --all --full-diff -p -- "*.json" | Select-String -Pattern "password|secret|private_key" -CaseSensitive
```

Add the approved institutional remote:
```powershell
git -C D:\Softfors\jup remote add origin <AUTHORIZED_PRIVATE_URL>
git -C D:\Softfors\jup remote -v
```

---

## Step 7 — Verify Environment (immediately before launch)

```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" -c "
import torch
assert torch.cuda.is_available(), 'CUDA not available'
print('CUDA device:', torch.cuda.get_device_name(0))
print('VRAM total (GiB):', round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1))
"
```

Run RC3 gate verification (synthetic, no training):
```powershell
D:\Softfors\jup\.venv\Scripts\python.exe -m pytest D:\Softfors\jup\tests\test_c1_launch_rc3.py -v
```
**Required:** 22/22 PASS before any launch attempt.

---

## Step 8 — Pilot Runtime Measurement (authorized bounded run)

Before committing all 6 runs, measure actual per-epoch wall time using a bounded pilot:
- Use the C1 training engine in synthetic mode for 1 epoch
- Record per-epoch time on the actual GPU
- Estimate total compute budget for 6 × N_epochs runs
- Confirm all 6 runs fit within the remaining compute window

Do not use synthetic pilot measurements as prospective results.

---

## Step 9 — Execute C1 Runs (in order)

After all gates pass, execute in this order:
1. `C1-T seed=42`
2. `C1-C seed=42`  ← matched control (same initial weights as 1)
3. `C1-T seed=123`
4. `C1-C seed=123`
5. `C1-T seed=3407`
6. `C1-C seed=3407`

Record every attempt (failed, interrupted, or complete) with timestamps and recovery hashes.

**Checkpoint selection:** use the pre-declared best-epoch selection rule from `src/training/phase20_selection.py`. Do not reselect post-hoc.

---

## Failure Handling

If fewer than 6 runs complete:
- Report partial results explicitly as partial
- Do not claim completed attribution
- Manuscript becomes bounded partial study
- Record exact failure cause and recovery hash

If all 6 complete but clock attestation expires mid-run:
- Runs that completed before expiry are valid
- Runs started after expiry: report the timestamp discrepancy
- Do not retroactively re-attest
