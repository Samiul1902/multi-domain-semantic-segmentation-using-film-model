# C1 — Final Launch-Boundary Design v1.0

Status: `DESIGN_ONLY__LAUNCH_NOT_ACTIVATED`
The production launch path is **not** activated, enabled, or reachable in this
task. No real-data driver is invoked. No approval is fabricated.

---

## 1. Current hard stop — exact inventory

Five independent refusal points exist today. All five must be addressed for a
launch-capable release; none is addressed by weakening the frozen package.

| # | Location | Mechanism | Effect |
|---|---|---|---|
| 1 | `readiness.py:91` | terminal `raise ReadinessError("C1_PREPARATION_ONLY_NO_REAL_DATA_DRIVER")` | `assert_launch_allowed` can never return, even with a fully-formed approval dict |
| 2 | `protocol.json` `execution.scientific_execution_enabled` | `false` | `run_real` raises `C1_FROZEN_PROTOCOL_EXECUTION_DISABLED` |
| 3 | `train_driver.py:run_real` | `verify_preparation()` → `assert_launch_allowed(protocol, approval, launch)` | unreachable body |
| 4 | `train_driver.py:real_loader_factory` | `assert_launch_allowed(protocol)` before importing any reader | data reader unreachable |
| 5 | `training_engine.py:Trainer.__init__` | non-synthetic → `assert_launch_allowed(load_protocol())` | CUDA Trainer unreachable |

Additionally `make_contract(..., synthetic=False)` requires `device="cuda"`,
so a real contract cannot be minted on CPU.

## 2. Binding constraint: the frozen package is immutable

`integration_contract.verify_preparation()` checks
`package_identities.json` against hard-coded SHA
`4660034d…c802b353`, then verifies every listed file. Editing
`readiness.py`, `control.py`, `protocol.json`, or the four planning documents
would break that chain and violate the no-frozen-modification rule.

Therefore the launch release **must be additive**. `protocol.json` must stay
byte-identical at `531e3eb2…087a61`. In particular
`scientific_execution_enabled` must **not** be flipped — flipping it changes
the protocol digest and invalidates the entire frozen identity chain.

Consequence: execution permission must be derived from a **separate
authorization artifact**, not from a protocol flag. This is consistent with the
protocol's own `separate_launch_required: true`.

## 3. Material gap found: incomplete executable identity

The frozen manifest binds only **3 of 8** `c1_film` modules:

| Module | Bound by frozen manifest |
|---|---|
| `__init__.py` | YES |
| `control.py` | YES |
| `readiness.py` | YES |
| `integration_contract.py` | **NO** |
| `recovery_store.py` | **NO** |
| `synthetic_fixture.py` | **NO** |
| `train_driver.py` | **NO** |
| `training_engine.py` | **NO** |
| `tests/test_c1_training_integration.py` | **NO** |

The five unbound modules are exactly the training-integration code added at
commit `ec51359`. `make_contract` records their hashes in `integration_sources`
and `validate_contract` recomputes that dict — but because there is **no
external frozen reference** for those hashes, the check is self-consistent, not
tamper-evident. An attacker who edits `training_engine.py` and regenerates a
contract produces a contract that validates.

This directly fails launch-requirement **1 (exact executable/source identity)**
and must be closed by an additive manifest, not by editing the frozen one.

## 4. Minimal change set for a launch-capable release

**Do not modify:** `readiness.py`, `control.py`, `__init__.py`, `protocol.json`,
`package_identities.json`, `src/models/film/global_medfilm.py`, any Phase-21
authority, any historical checkpoint, BARR-M1 RC1.

### 4.1 New additive package — `src/research/c1_film_launch/`

| File | Purpose |
|---|---|
| `manifest_v2.json` | Additive executable manifest binding **all 8** `c1_film` modules + both C1 test files + the launch package itself + protocol digest + recipe digest + dependency spec digest. Written once, hash-published before approval. |
| `release_identity.py` | Computes the **release digest** = SHA-256 over (manifest_v2 digest, protocol digest, architecture digest, dependency-spec digest, interpreter identity, torch build, CUDA build). This is the single identity that approval must name. |
| `launch_gate.py` | `assert_launch_authorized(auth, instruction, release)` — implements the ten checks in §5. Raises on any failure. Never falls open. |
| `launch_driver.py` | The **only** module permitted to construct a real `Trainer`. Mints an opaque `LaunchGrant` and passes it down. |

### 4.2 Two minimal edits to unbound (therefore editable) modules

**`training_engine.py`** — replace the unconditional preparation-gate call:

```
# current
if contract["mode"] != "SYNTHETIC_ONLY":
    from .readiness import assert_launch_allowed, load_protocol
    assert_launch_allowed(load_protocol())          # always raises

# launch release
if contract["mode"] != "SYNTHETIC_ONLY":
    if grant is None:
        raise ReadinessError("C1_LAUNCH_GRANT_REQUIRED")
    grant.verify()                                   # bound to release digest
```

`grant` defaults to `None`, so every existing synthetic call site and all 34
tests keep their current behaviour unchanged.

**`train_driver.py`** — `run_real(arm, seed, *, grant)`:
- keep `verify_preparation()` as a **precondition** (frozen package must still
  be intact),
- delete the `scientific_execution_enabled` branch (it is a definition
  document flag, not an authorization),
- call `assert_launch_authorized(...)` from `launch_gate`, not the preparation
  gate,
- keep `torch.cuda.is_available()` guard.

`real_loader_factory` similarly swaps its gate call for the launch gate.

### 4.3 What is deliberately NOT changed

- No batch size, resolution, LR, optimizer, scheduler, AMP, seed, arm,
  population, selection rule, or threshold change.
- No TEST or ROUTER_HOLDOUT path is introduced; the loader factory continues to
  read only `TRAIN` and `VAL` from the frozen protocol, and
  `create_loader` independently rejects `split == "TEST"`.
- No BARR-M1 artifact is read or reused.
- The preparation driver `readiness.main()` keeps reporting
  `scientific_execution: NOT_STARTED`.

## 5. Ten mandatory launch verifications

The launch gate must verify all ten. Any single failure aborts.

| # | Requirement | Concrete check |
|---|---|---|
| 1 | Exact executable/source identity | Recompute `manifest_v2` over all 8 modules + tests + launch package; compare to published release digest. Also re-run `verify_preparation()` so the frozen chain is intact. |
| 2 | C1-specific scientific authorization | `auth.scope == "C1_FILM_ATTRIBUTION_V1"`; `auth.protocol_sha256 == 531e3eb2…`; `auth.release_digest == release.digest`; required institutional fields non-empty. **`scope == "BARR-M1"` must be rejected explicitly.** |
| 3 | Frozen treatment/control definitions | `arms == {"C1-T","C1-C"}`; parameter accounting re-derived at runtime equals 3,523,001 / 3,432,233 / 90,768; `verify_identity_control` passes on the control before epoch 1. |
| 4 | Frozen protocol identity | `hashlib.sha256(protocol.json) == 531e3eb2…`; `study_id`, `seeds`, `dataset`, `recipe` deep-equal the frozen values. |
| 5 | Approved seed list | `auth.seeds == [42, 123, 3407]` and the run plan contains exactly those 6 (arm × seed) combinations — no more, no fewer. |
| 6 | Approved populations | `TRAIN` = `manifests/phase4_v3/train.csv`, n=5832, SHA `28702fc3…`; `VAL` = `val.csv`, n=808, SHA `082c80b2…`; manifest bytes re-hashed on disk; TRAIN∩VAL sample_id = ∅. |
| 7 | TEST / ROUTER_HOLDOUT prohibition | `EXCLUSIONS ⊇ {TEST, ROUTER_HOLDOUT, EXTERNAL, QUARANTINE, BARR-M1, C2, C3}`; no resolved path under any `test`/`router_holdout`/`external`/`quarantine` manifest; `create_loader` TEST rejection still active. |
| 8 | Resource and aggregate training budget | `logical_runs == 6`; `max_epochs ≤ 100`; cumulative `active_seconds ≤ 96 h` enforced per run and summed across the six; free disk re-measured ≥ 3× worst-case aggregate (≈75 GiB). |
| 9 | Checkpoint/recovery integrity | `EpochStore` pointer + SHA verify; `writer_lock` exclusive; `restore()` contract/identity/selection replay; `C1_CUDA_RNG_TOPOLOGY_CHANGED` guard. Must be exercised on synthetic data at the **production worker configuration** (§6.3). |
| 10 | Separate explicit launch instruction | A distinct artifact whose `authorization_id` matches the approval but whose `launch_id` is unique, issued **after** the release digest exists, naming the exact release digest and the exact six runs. Absence → `C1_SEPARATE_LAUNCH_REQUIRED`. |

## 6. Ordering constraint — artifact identity precedes approval

The release must be finalized and identified **before** approval is attached.
The admissible sequence is strictly:

1. Build `c1_film_launch/`, write `manifest_v2.json`.
2. Compute and publish the **release digest**.
3. Obtain C1-specific scientific authorization that names that digest.
4. Obtain a separate launch instruction that names that digest and the six runs.
5. Execute.

Any reordering — approval first, or an approval that names a digest computed
afterwards — is inadmissible, because the approval would not bind the code that
actually runs. Any post-approval edit to a bound file changes the digest and
voids the approval; a new digest requires a new approval.

## 7. Explicit non-authorizations

- This design does not authorize training.
- This design does not reuse BARR-M1 authorization (scope check rejects it).
- `assert_launch_allowed` remains frozen and continues to raise unconditionally
  in the preparation package.
- No launch artifact is created in this task; only its specification.
