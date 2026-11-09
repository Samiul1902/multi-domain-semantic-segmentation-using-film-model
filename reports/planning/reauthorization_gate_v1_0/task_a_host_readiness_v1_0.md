# Task A — Host Readiness Diagnostics

**Classification:** `RA_MEDFILM_BARR_HOST_READINESS_DIAGNOSTICS`
**Version:** 1.0
**Measured local:** 2026-10-26T22:41–22:44 (+06:00)
**Mode:** read-only. No configuration changed, no service restarted, no device installed, no training launched.

**Clock caveat applying to every timestamp in this document:** the host clock is **not synchronised** (see §1). Absolute wall-clock values carry an unquantified offset. Only *relative* ordering and *elapsed* quantities measured within this session are trustworthy. Event-log timestamps that fall before the last clock correction are shifted by the offset recorded in §2 and must not be read as true times.

---

## 1. Time synchronisation — NOT ESTABLISHED

```
w32tm /query /status
  Leap Indicator: 3(not synchronized)
  Stratum: 0 (unspecified)
  Source: Local CMOS Clock
  Last Successful Sync Time: unspecified
  Poll Interval: 10 (1024s)
```

```
w32tm /query /peers
  Peer: time.windows.com,0x9
  State: Pending
  Time Remaining: 26235 s (~7.3 h)
```

| Item | Observed | Assessment |
|---|---|---|
| Leap indicator | `3(not synchronized)` | **Not synchronised** |
| Time source | `Local CMOS Clock` | Free-running RTC, no NTP discipline |
| Last successful sync | `unspecified` | No sync currently registered |
| Configured peer | `time.windows.com,0x9` | Correct peer, but `Pending` |
| `w32time` service state | `Running` | Running |
| `w32time` start type | **`Manual`** (registry `Start=3`) | **Defect** — should be `Automatic` |
| Time provider type | `NTP` | Correct for a workstation |
| `SpecialPollInterval` | **`32768` s (9.1 h)** | **Defect** — very long; drift accrues between polls |

**Verdict: time synchronisation is NOT working and is NOT reported as working.** The service runs but is configured `Manual`, polls every ~9 hours, and currently sits `Pending` with no successful sync registered.

Note: `Time-Service` event **ID 158** recurs every ~17 minutes. Its message is *"The time provider 'VMICTimeProvider' has indicated that the current hardware and operating environment is not supported… This behavior is expected for VMICTimeProvider on non-HyperV-guest environments."* **This is benign** and is not the cause of the sync failure. It is recorded here so it is not mistaken for a defect.

---

## 2. RTC stability — PHYSICAL FAULT CONFIRMED, NOT REMEDIATED

The clock has repeatedly required large step corrections. Each value below is a **measured** `Time-Service` **event ID 52** message (*"The time service has set the time with offset N seconds"*):

| Event timestamp (host clock) | Offset applied | Offset in days |
|---|---:|---:|
| 2026-10-22 10:48:18 | 151,916 s | 1.758 |
| 2026-10-25 19:11:17 | 441,283 s | 5.107 |
| 2026-10-25 21:08:33 | **448,320 s** | **5.189** |

**Interpretation.** Between 2026-10-22 10:48 and 2026-10-25 19:11 (3.35 days of clock time) the required offset grew from 1.76 d to 5.11 d — an increase of ~3.35 d. The clock was therefore losing essentially **all** elapsed time across that interval. This is the signature of an RTC that does not hold time across power-off, i.e. a **depleted/failed CMOS battery**.

**Corroborating boot evidence.** `Win32_OperatingSystem.LastBootUpTime = 2026-10-25 21:08:14`, matching the offset correction at `21:08:33`. Subtracting the 448,320 s offset from the corrected time gives `2026-10-20 16:36:33` — which is exactly where the apparent "10/20 16:35–16:36" `Kernel-Power 41` cluster sits. **That cluster is not a separate power-loss event; it is the pre-correction stamp of the same 2026-10-25 21:08 boot.**

**Since the last correction.** No `ID 52` offset has been applied since 2026-10-25 21:08:33, which suggests the clock has held reasonably *while powered on*. But with the service unsynchronised, absolute accuracy is **unverified**.

**Verdict: the RTC fault is real, diagnosed, and NOT remediated.** No evidence exists that the CMOS battery has been replaced — offsets of this magnitude continued through 2026-10-25, and the mechanism (time lost across power-off) is unchanged.

---

## 3. Power-event history — CHRONIC, NOT REMEDIATED

| Query | Result |
|---|---|
| `Kernel-Power` ID 41 (unexpected shutdown), retention | **87 events** |
| Oldest | 2026-08-05 19:48:34 (stamped) |
| Newest | 2026-10-20 16:36:20 (stamped — the pre-correction stamp of the 10/25 boot) |
| `EventLog` ID 6008 (unexpected shutdown) | Present, same clusters |
| ID 41 **since current boot** (2026-10-25 21:08:14) | **0** |
| Current uptime | **1 d 01 h 33 m** at measurement |

**Interpretation.** 87 unexpected-shutdown events since August is roughly one per day over 82 days and indicates chronic power-delivery instability. The **current** boot is clean (0 events in ~25.5 h), so the machine is presently stable — but stability across one boot is not evidence of a fix.

**Caveat on count.** Because pre-correction event stamps are shifted, individual timestamps cannot be attributed to true calendar times, and closely-spaced duplicates may represent repeated boot attempts within one power event rather than distinct losses. The **87 total and the presence of the events** are reliable; the **per-event true times are not.**

**Verdict: no evidence that power-delivery instability has been remediated.** No UPS is present (§4).

---

## 4. Power hardware — NO UPS, NO BATTERY

| Check | Result |
|---|---|
| `Win32_Battery` device count | **0** |
| `Win32_SystemEnclosure.ChassisTypes` | `3` → **Desktop** |
| Devices matching `UPS|Battery|Power` | `ACPI Power Button`, `PCI Express Upstream Switch Port` only |
| Active power plan | `Balanced` |

A desktop has no internal battery, so `Win32_Battery = 0` is expected and is not itself a fault. The relevant finding is that **no UPS or battery-backed power device is enumerated**. Many consumer UPS units do not enumerate over USB/HID, so this is not proof of absence — but it is also **not evidence of presence**.

**Verdict: UPS installation is NOT established.** Reporting it as installed would require at minimum a device enumeration or vendor-agent telemetry. Neither exists.

---

## 5. GPU and compute environment — HEALTHY

```
nvidia-smi
  NVIDIA GeForce RTX 3060 Ti   WDDM   00000000:0A:00.0
  Driver 610.88 · CUDA UMD 13.3
  8192 MiB total · 568 MiB used · 49 °C · 12% util · P5 · 33 W / 265 W
```

| Item | Value | Assessment |
|---|---|---|
| GPU | NVIDIA GeForce RTX 3060 Ti | Healthy |
| VRAM | 8,192 MiB (568 MiB in use) | **8 GB is the binding constraint for batch-4 512² training** |
| Driver | 610.88 | Current |
| Temperature | 49 °C idle | Normal |
| Driver model | WDDM | Fine for compute |
| Second adapter | Parsec Virtual Display Adapter | Remote-access display, not compute |
| PyTorch | 2.6.0+cu124, CUDA available, cuDNN 90100 | Working |
| Python (venv) | 3.11.9 | Consistent with prior phases |
| RAM | 31.9 GB | Adequate |
| Disk `D:` (repo) | 128.9 GB free of 931.5 GB | Adequate for checkpoints |

**Verdict: no GPU remediation required.**

---

## 6. What still requires physical remediation

| ID | Item | Status | Evidence basis |
|---|---|---|---|
| **P1** | **Replace CMOS / RTC battery** | **NOT DONE** | Offsets of 1.76 → 5.11 → 5.19 days at successive boots; time lost across power-off; no post-replacement offset observed |
| **P2** | **Install UPS / battery-backed power** | **NOT DONE** | 87 `Kernel-Power 41` events since 2026-08-05; no UPS device enumerated |
| **P3** | **Remediate power delivery** (mains, PSU, cabling) | **NOT DONE** | Chronic unexpected shutdowns; cause not isolated |
| **S1** | Fix `w32time` start type → `Automatic` | **NOT DONE** | `Start=3` (Manual) |
| **S2** | Reduce `SpecialPollInterval` and verify a held sync | **NOT DONE** | 32,768 s poll; peer `Pending`; no successful sync registered |

**P1–P3 are physical and require the operator.** S1–S2 are software configuration and can be done in minutes, but they **cannot compensate for a dead RTC** — a correct NTP configuration on a host that loses five days per power cycle will still boot with a wrong clock and will still stamp early-boot events incorrectly.

**Nothing in this section is reported as complete.** No claim of battery replacement, UPS installation, or time synchronisation is made anywhere in this work package, because no evidence supports any of them.

---

## 7. Readiness verdict

| Dimension | Ready? |
|---|---|
| GPU / CUDA / PyTorch stack | **YES** |
| RAM / disk | **YES** |
| Clock accuracy (absolute) | **NO** — unsynchronised |
| RTC holds time across power-off | **NO** — confirmed fault |
| Power stability | **NO** — chronic, unmitigated |
| Unattended multi-day run safety | **NO** — no UPS, 87 unexpected shutdowns in retention |

**A multi-day unattended training run on this host today would be expected to be interrupted**, on the evidence of 87 prior unexpected shutdowns and no UPS. Any work order that assumes uninterrupted multi-day compute must treat P1–P3 as blocking prerequisites, not as parallel housekeeping.

---

*End of Task A. Read-only: no service reconfigured, no device installed, no training launched.*
