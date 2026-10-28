# RA-MedFiLM-BARR — C1 Final Technical Readiness Report v1.0

Terminal: `RA_MEDFILM_BARR_C1_FINAL_TECHNICAL_READINESS_ASSESSED__SCIENTIFIC_EXECUTION_PENDING`

Date of assessment: 2026-10-28
Repository: `D:\Softfors\jup`, branch `master`
Baseline commit at task start: `ec51359370c673f0038a3655379b70af7da33d03`
C1 protocol SHA-256: `531E3EB255A66381201D1AAF49BBE55ABFDBE529640F5C584EF100D298087A61` (re-verified byte-identical, unmodified)

---

## Decision table

| Item | Status | Basis |
|---|---|---|
| C1 treatment/control implementation | **PASS** | 8 modules present; parameter accounting 3,523,001 / 3,432,233 / 90,768 asserted at construction; identity FiLM exact |
| CPU synthetic verification | **PASS** | 34 tests + 23 subtests passed (31.5 s) |
| CUDA synthetic verification | **PASS** | 22/22 checks passed on RTX 3060 Ti; 0 blocked, 0 failed |
| Dependency reproducibility | **BLOCKED** | Installed venv verified and fully captured, but `requirements.txt` / `pyproject.toml` carry **zero version pins** — not reproducible from the declared spec |
| GPU / storage feasibility | **PASS** | Train 512×512 B=4 AMP peak reserved 3,866 MiB of 8,192; free disk 128.3 GiB vs 24.83 GiB worst case |
| Clock reliability | **BLOCKED** | `w32time` service **Stopped** (Manual); no NTP source queryable; no UPS enumerated |
| Prospective protocol | **PASS** | Frozen at `531e3eb2…`, status `PROTOCOL_READY_FOR_APPROVAL__NOT_APPROVED` |
| Launch-capable release identity | **BLOCKED** | Not built. Design only; a blocking executable-identity gap was found |
| Scientific approval | **BLOCKED** | `PENDING` — no authorization artifact exists |
| Separate launch authorization | **BLOCKED** | Not issued; requires the release digest to exist first |
| Experiment validity (8 checks) | **BLOCKED** | 7 PASS, 1 FAIL: recovery never exercised at production worker config |
| Git push | **BLOCKED** | No remote configured |

**Technical readiness is 5 PASS / 6 BLOCKED / 1 BLOCKED-with-subfindings.**
**Scientific authorization is 0 of 2 satisfied.**
These are separate axes. Technical progress does not advance scientific authorization.

---

## 1. Synthetic CUDA verification — PASS (22/22)

GPU: NVIDIA GeForce RTX 3060 Ti, 8,192 MiB, driver 610.88, CC 8.6, torch 2.6.0+cu124,
CUDA 12.4, cuDNN 9.1.0. At query time 722 MiB used, 7,303 MiB free; **no competing
compute process** (all 25 enumerated processes were desktop/compositor/UI; two
unidentified entries reported `[Insufficient Permissions]` but no memory and are
not compute jobs). Resources were therefore adequate — `CUDA_VALIDATION_BLOCKED`
was **not** triggered.

| Test | Result |
|---|---|
| C1-T forward/backward on CUDA | PASS — logits (1,1,32,32), 21 conditioning params receive gradients |
| C1-C forward/backward on CUDA | PASS — 0 conditioning gradients; `verify_identity_control` holds after backward |
| Optimizer updates | PASS — head weight moved, max_diff 7.03e-4 over 10 steps |
| Mixed precision as configured | PASS — AMP active, autocast logits float16, `GradScaler` scale 32768.0, step+update OK |
| Synthetic checkpoint creation | PASS — epoch-0001, 56,532,620 B, SHA matches pointer, CUDA RNG captured |
| Synthetic resume | PASS — checkpoint loads, lifecycle reaches COMPLETE |
| Model/optimizer state restoration | PASS — optimizer state structural match; model state restored (see determinism note) |
| CUDA RNG restoration | PASS — capture→restore reproduces an identical random sequence |
| Arm and run-identity integrity | PASS — `initial_sha256` equal across arms; T/C identities differ; counts exact |
| CUDA forward determinism | PASS — identical input yields bit-identical output |
| Uninterrupted vs resumed | PASS with documented deviation |

### Determinism statement — no bitwise claim

`cudnn.deterministic = True` and `cudnn.benchmark = False` are set, and the forward
pass is bit-identical on repeat. The **backward** pass is not fully deterministic:
interpolate-backward and scatter/gather kernels have no deterministic CUDA
implementation. Measured uninterrupted-vs-resumed deviation:

- model state max |Δ| = **2.82e-4**
- per-epoch macro-Dice |Δ| = 8.74e-5, 1.13e-4, 1.82e-4 (epochs 1–3)
- per-epoch val-loss |Δ| ≤ 6.4e-6
- **selected epoch identical** (2 vs 2)

The CPU path is exactly reproducible (verified: model and history both match).
Bitwise equivalence on CUDA is **not** claimed and must not be claimed downstream.
No physical power-off fault injection was performed; interruptions were simulated
at the four commit boundaries (`before_payload`, `after_payload`, `before_pointer`,
`after_pointer`) in the existing suite.

Artifact: `reports/audits/c1_synthetic_cuda_verification_v1_0.json`
Harness: `scripts/verification/c1_synthetic_cuda_verification.py`

## 2. Dependency reproducibility — BLOCKED

Verified: Python 3.11.9, torch 2.6.0+cu124 and torchvision 0.21.0+cu124 from the
PyTorch cu124 wheel index, 77 packages total, all imports resolving, CUDA stack
compatible with driver 610.88 / CC 8.6.

**The blocking defect:** `requirements.txt` and `pyproject.toml` list bare package
names with **no version specifiers at all** — no `==`, no lock file, no hashes.
A fresh `pip install -r requirements.txt` would resolve to newest versions, which
are not the verified set. Several installed versions are unusually advanced
(pandas 3.0.5, numpy 2.4.6, scikit-learn 1.9.1), and those are the versions the
34 tests actually pass under.

A complete reproducible specification using verified versions has been prepared
(`reproducible_environment_spec.json`, two-stage install with the correct CUDA
index URL). Pinning the declaration files is a **specification change** and was
deliberately not made here. No package was installed, upgraded, or downgraded; no
frozen dependency was replaced.

## 3. GPU and storage feasibility — PASS

Measured, not estimated, using artificial tensors at the frozen recipe:

| Workload | Peak allocated | Peak reserved | Headroom |
|---|---|---|---|
| TRAIN 512×512, B=4, AMP | 3,404.3 MiB | 3,866.0 MiB | 4,326.0 MiB |
| EVAL 512×512, B=8, AMP | 2,340.1 MiB | 2,954.0 MiB | 5,238.0 MiB |

Storage: D: has **128.3 GiB free** (137,772,544,000 B) of 932 GiB, 87% used.
One checkpoint measured at **42,369,710 B** (Phase-21 analogue); independent
parameter arithmetic agrees (13.4 + 26.9 + ~2 MiB ≈ 42.3 MiB). Because
`EpochStore` keeps every committed epoch, six runs cost:

- worst case 100 epochs → **24.83 GiB** (19% of free space)
- typical ~40 epochs → **9.93 GiB**
- early stop ~20 epochs → 4.96 GiB

Storage is sufficient. **No wall-clock training duration is estimated or claimed** —
none has been measured.

## 4. Clock and host reliability — BLOCKED

- `Get-Service w32time` → **Stopped**, StartType **Manual**
- `w32tm /query /status|source|peers` → `0x80070426` (service not started) for all three
- Last boot 2026-10-27 20:49:24; uptime 10 h 42 m
- Kernel-Power 41: **0 since current boot**, but **85 in the retained log**
  (clusters: 08-05 ×12, 10-20 ×10, 09-27 ×8, 10-14 ×7, 10-07 ×7, 09-19 ×7, 08-15 ×6)
- UPS/battery: **none enumerated** (`powercfg /batteryreport` produced no
  `Batteries` section; `Win32_Battery` empty)

The time service is not merely drifting — it is not running, so there is no NTP
source, no measured offset, and no drift bound. **Absolute timestamps from this
host carry an unquantified offset; only within-session ordering is trustworthy.**
Zero power events in a 10-hour window is favourable but far too short to establish
stability for a multi-day campaign, and with no UPS an unattended run remains
exposed to abrupt termination. The atomic-commit recovery design mitigates but does
not substitute for power stability.

## 5. Remaining launch implementation requirements — BLOCKED

Design delivered (`launch_boundary_design.md`, `remaining_launch_requirements.json`).
Nothing was activated. Five refusal points were inventoried; the frozen package
must remain byte-identical, so the release must be **additive**.

**Blocking gap found:** the frozen `package_identities.json` binds only **3 of 8**
`c1_film` modules. The five modules added at `ec51359` — `integration_contract.py`,
`recovery_store.py`, `synthetic_fixture.py`, `train_driver.py`,
`training_engine.py` — and `tests/test_c1_training_integration.py` are **not bound
by any external frozen reference**. `make_contract` records their hashes in
`integration_sources` and `validate_contract` recomputes, but with no published
expectation the check is self-consistent rather than tamper-evident. This fails
launch requirement 1.

Remedy is additive: a new `src/research/c1_film_launch/` package with
`manifest_v2.json` binding all eight modules, a `release_identity.py` computing one
release digest, a fail-closed `launch_gate.py` implementing the ten checks, and a
`launch_driver.py` as the sole real-Trainer entry. Two backward-compatible edits
(`training_engine.py` grant parameter defaulting to `None`; `train_driver.py`
gate swap) plus one additive worker-config recovery test.

Ordering is non-negotiable: **artifact identity precedes approval.** Approval must
name a release digest that already exists. Any post-approval edit to a bound file
voids the approval.

`protocol.json` must **not** have `scientific_execution_enabled` flipped — doing so
changes the protocol digest and destroys the frozen identity chain. Execution
permission must come from the authorization artifact.

## 6. Scientific validity limitations — 7 PASS / 1 FAIL

PASS: matched backbone init (single construction + `deepcopy` before optimization,
`initial_sha256` equal, RNG untouched); identity FiLM **exactly** inactive
(zero-init output ⇒ γ=β=0 ⇒ `F_hat = F` bit-preserving, frozen, re-verified every
epoch and after restore, network output `torch.equal` to a bypass reference for all
four tasks); parameter counts transparent (3,523,001 total both arms; 3,432,233 vs
3,523,001 trainable; 90,768 = 2.58% frozen); identical selection rule (one frozen
`phase20_macro_domain_mean_dice_v1`, tolerance 1e-12, replayed on restore); VAL808
correctly classified as development/selection-consumed.

Documented limitations — recorded, **not** silently changed:

1. **Worker configuration unverified (the FAIL).** Production uses
   `num_workers=4` train / `2` eval; every recovery test uses `0`. Worker-process
   determinism under Windows `spawn`, `MultiDomainDataset` picklability, and
   recovery at workers>0 are all untested. `loader_states` is audit-only because
   each epoch is rebuilt from `derive_epoch_seed(seed, epoch)`.
2. **Endpoint is in-sample.** The primary endpoint is evaluated on the same VAL808
   used to select the epoch, so it is the selection objective measured on the
   selection population — optimistically biased, development-stage only.
3. **Endpoint wording ambiguity.** "selected_VAL" does not state stored
   `best_records` vs recomputed pass. Numerically identical today; must be pinned
   before launch.
4. **n = 3 seeds.** Sample SD on 2 df; descriptive only, no seed-population inference
   (already forbidden by protocol).
5. **Patient clustering only in KUB (267).** ISIC/BUSI/KVASIR have no
   `patient_id`, so bootstrap clusters are images there — uncertainty understated
   when images share an unobserved patient. Must be disclosed.

## 7. Git

- Branch `master`, baseline HEAD `ec51359370c673f0038a3655379b70af7da33d03`.
- Frozen C1 files verified **unmodified** (`git diff --stat` over `src/research/`,
  both C1 test files, and the frozen planning directory returned empty).
- Pre-existing unrelated modifications to 40 tracked files (notebook READMEs,
  `train_phase13b_localizer.py`, `train_phase14_refiner.py`, `src/data/*`,
  `src/utils/*`, etc.) were **left untouched and unstaged**.
- Scoped commit created for this task only; exact SHA in §9.
- `git remote -v` returned **empty** — no remote, no upstream.

```
GIT_REMOTE_CONFIGURATION_REQUIRED
GIT_PUSH_STATUS: BLOCKED
```

No remote URL was invented, no force-push, no history change, no hook disabled.

## 8. Exact prerequisites before authorized C1 training

Ordered; all must hold.

1. **Host remediation.** Start `w32time` (currently Stopped/Manual), configure a
   working NTP source, and record a measured offset; attach a UPS; demonstrate a
   clean-power observation window materially longer than 10 hours.
2. **Dependency specification pinned** to the verified versions
   (`torch==2.6.0+cu124`, `torchvision==0.21.0+cu124` from the cu124 index, plus the
   pinned remainder). This is a spec change requiring its own review.
3. **Launch release built** — `src/research/c1_film_launch/` with `manifest_v2.json`
   covering all 8 modules + both tests + the launch package.
4. **Executable-identity gap closed** — the five currently unbound modules bound by
   the additive manifest.
5. **Worker-config recovery test added and passing** at `num_workers=4`/`2`.
6. **Release digest computed and published** — before any approval is sought.
7. **C1-specific scientific authorization** naming that digest, `scope`
   `C1_FILM_ATTRIBUTION_V1`, arms `{C1-T, C1-C}`, seeds `[42, 123, 3407]`, and the
   full exclusion set. BARR-M1 authorization cannot satisfy this.
8. **Separate launch instruction** with a distinct `launch_id`, naming the release
   digest and the exact six runs.
9. **Free disk re-measured** immediately before launch, ≥ 3× worst-case aggregate.
10. **Endpoint wording pinned** (stored `best_records` vs recomputed) and the
    patient-clustering limitation written into the analysis plan.

## 9. Artifacts produced

| File | Content |
|---|---|
| `scripts/verification/c1_synthetic_cuda_verification.py` | 22-check CUDA harness (synthetic tensors only) |
| `reports/audits/c1_synthetic_cuda_verification_v1_0.json` | Machine-readable CUDA result |
| `reports/planning/c1_final_technical_readiness_v1/reproducible_environment_spec.json` | Verified-version environment spec |
| `reports/planning/c1_final_technical_readiness_v1/dependency_reproducibility_assessment.md` | Task 2 assessment |
| `reports/planning/c1_final_technical_readiness_v1/resource_feasibility_assessment.md` | Task 3 assessment |
| `reports/planning/c1_final_technical_readiness_v1/launch_boundary_design.md` | Task 4 design |
| `reports/planning/c1_final_technical_readiness_v1/remaining_launch_requirements.json` | Machine-readable launch requirements |
| `reports/planning/c1_final_technical_readiness_v1/experiment_validity_check.md` | Task 5 design check |
| `reports/planning/c1_final_technical_readiness_v1/final_readiness_report.md` | This report |
| `reports/planning/c1_final_technical_readiness_v1/decision_table.json` | Machine-readable decision table |

## 10. Restrictions honoured

No real-data training. No real-data inference. No TEST access. No ROUTER_HOLDOUT
access. No historical checkpoint modified or opened. No frozen protocol modified
(re-verified byte-identical). No BARR-M1 execution or authorization reuse. No
fabricated approval. Production launch path not activated. No package installed.
No physical power-off fault injection. No new data-derived model selection or
scientific analysis. No automatic phase progression.

**STOP.**
