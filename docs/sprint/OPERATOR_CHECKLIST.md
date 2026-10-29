# External Operator Action Checklist for C1 Production Launch

**Authority Requirement:** Must be executed by a human institutional operator / supervisor.  
**Strict Prohibition:** Never fabricate signatures, authorities, or hardware clock proofs.

---

### Step 1: Windows Hardware Clock & NTP Synchronization
1. Ensure the CMOS battery is functional and system hardware clock is synchronized.
2. In an administrative PowerShell console, synchronize the Windows Time Service:
   ```powershell
   w32tm /resync /force
   w32tm /query /status
   ```
3. Verify that the local clock offset is within $\pm 1.0$ second against an official stratum-1 NTP source.

### Step 2: Uninterruptible Power & Thermal Protection
1. Ensure the workstation containing the NVIDIA RTX 3060 Ti GPU is backed by an Uninterruptible Power Supply (UPS) with at least 20 minutes of runtime headroom.
2. Verify fan curves and airflow: peak VRAM temperature should remain $< 80^\circ\text{C}$ under full training load.

### Step 3: Verified Python Environment Verification
1. Activate project virtual environment:
   ```powershell
   & "D:\Softfors\jup\.venv\Scripts\Activate.ps1"
   ```
2. Verify PyTorch with CUDA 12.4 support:
   ```powershell
   python -c "import torch; assert torch.cuda.is_available(); print('CUDA Device:', torch.cuda.get_device_name(0))"
   ```

### Step 4: Provision Production Keystore
1. Create an isolated production keystore directory with strict Windows ACLs (read/write access restricted to the operator account only):
   ```powershell
   icacls "D:\Softfors\jup\keystore" /inheritance:r /grant:r "$($env:USERNAME):(OI)(CI)F"
   ```
2. Generate genuine ECDSA-P256 keypairs for `RELEASE_AUTHORITY`, `TIME_AUTHORITY`, and `LAUNCH_AUTHORITY`.
3. Sign the C1 scientific launch authorization binding:
   - Study ID: `c1_film_attribution_v1`
   - Protocol SHA-256: `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61`
   - Run plan: Exactly 6 runs (`(C1-T, 42)`, `(C1-C, 42)`, `(C1-T, 123)`, `(C1-C, 123)`, `(C1-T, 3407)`, `(C1-C, 3407)`).

### Step 5: Issue Signed Launch Instruction
1. Issue a separate, single-use signed launch token binding the active hardware clock status proof.
2. Store the signed approval record in the designated production gate directory.

### Step 6: Configure Private GitHub Remote
1. Verify confidentiality and absence of sensitive credentials across all files.
2. Add the approved private institutional GitHub remote:
   ```powershell
   git -C "D:\Softfors\jup" remote add origin <AUTHORIZED_PRIVATE_URL>
   git -C "D:\Softfors\jup" remote -v
   ```
