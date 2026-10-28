# C1 Launch Release Candidate — Release Identity Report

```
LAUNCH_RELEASE_ID   C1_FILM_ATTRIBUTION_V1_LAUNCH_RC1
STUDY_ID            C1_FILM_ATTRIBUTION_V1
RELEASE_DIGEST      1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1
MANIFEST_SHA256     0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe
BOUND_SOURCES       33
C1_MODULES_BOUND    8 / 8
LAUNCH_SOURCES      4 / 4
PROTOCOL_SHA256     531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61
ARCHITECTURE_SHA256 a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f
RECIPE_DIGEST       275f20a935d6b78342306166ff067eae88ad1b6baaf9ed2a6ab786bba281f14c
DEPENDENCY_LOCK     b4cdea3ab219db05d26725c74f2dbe42955a3cbe4daaba9f3b296ac201b0b36d
SCIENTIFIC_EXECUTION  NOT_AUTHORIZED
```

This digest was computed **before** any scientific approval was requested, as
required. No approval exists.

---

## 1. Manifest design — no circular hashing

`manifest_v2.json` binds every executable source by explicit `path → sha256`.
It does **not** contain its own digest and does **not** bind itself:

```
self_excluded = ["src/research/c1_film_launch/manifest_v2.json",
                 "src/research/c1_film_launch/RELEASE_DIGEST.txt"]
```

`verify_release()` enforces that invariant (`C1_RELEASE_SELF_BINDING` if violated),
so the exclusion is checked, not merely asserted.

**Release digest rule** (published, independently recomputable):

```
sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, allow_nan=False).encode("utf-8"))
```

Two identities are published and both are checkable:

| Identity | Covers | Purpose |
|---|---|---|
| `release_digest` | semantic content of the manifest | survives reformatting |
| `manifest_sha256` | manifest file bytes | detects any byte edit |

## 2. Required coverage is declared in code, not in the manifest

`release_identity.REQUIRED_COVERAGE` lists the mandatory paths. `verify_release()`
asserts the manifest covers them and raises `C1_RELEASE_COVERAGE_INCOMPLETE`
otherwise. A manifest that silently omits `recovery_store.py` therefore fails —
demonstrated by `test_missing_module_coverage_detected`.

This matters because the frozen `package_identities.json` binds only
`__init__.py`, `control.py` and `readiness.py`. The five modules added at
`ec51359` had no external frozen reference; they now do.

## 3. File inventory (33 bound sources)

### C1 implementation modules — 8
| SHA-256 (12) | Bytes | Path |
|---|---|---|
| `ef50694b3062` | 84 | `src/research/c1_film/__init__.py` |
| `c2fc3bac59c5` | 4,264 | `src/research/c1_film/control.py` |
| `cedbe01f534b` | 3,436 | `src/research/c1_film/integration_contract.py` |
| `97442c17bfb8` | 4,889 | `src/research/c1_film/readiness.py` |
| `5c2d46f6ab1f` | 4,633 | `src/research/c1_film/recovery_store.py` |
| `9baffa4f50df` | 2,510 | `src/research/c1_film/synthetic_fixture.py` |
| `eab54540a2a3` | 5,472 | `src/research/c1_film/train_driver.py` |
| `9c71cf4667b1` | 14,660 | `src/research/c1_film/training_engine.py` |

`control.py` and `readiness.py` hashes are **identical to the frozen
`package_identities.json` values**, confirming the frozen package was not altered.

### Launch package — 4
| SHA-256 (12) | Bytes | Path |
|---|---|---|
| `e6a05be0b2d0` | 1,261 | `src/research/c1_film_launch/__init__.py` |
| `64a0b2f6ceee` | 2,198 | `src/research/c1_film_launch/launch_driver.py` |
| `fb17a86502a0` | 20,345 | `src/research/c1_film_launch/launch_gate.py` |
| `77690ebb43ab` | 10,226 | `src/research/c1_film_launch/release_identity.py` |

### C1 tests — 4
| SHA-256 (12) | Bytes | Path |
|---|---|---|
| `19a79e15bcbd` | 9,536 | `tests/test_c1_film_preparation.py` |
| `3dc4f6c82ecb` | 15,622 | `tests/test_c1_training_integration.py` |
| `338b1eeb90b3` | 25,007 | `tests/test_c1_launch_release.py` |
| `624616d887ce` | 10,663 | `tests/test_c1_launch_multiprocessing.py` |

### Result-affecting dependencies — 11
| SHA-256 (12) | Bytes | Path |
|---|---|---|
| `a04ff3e61b4d` | 12,458 | `src/models/film/global_medfilm.py` |
| `3df73eaa3439` | 566 | `src/models/film/__init__.py` |
| `a59782f1aa85` | 3,458 | `src/data/domain_balanced_sampler.py` |
| `eb0c1b5d295d` | 1,345 | `src/data/loaders.py` |
| `461062e5d6bf` | 5,969 | `src/data/multidomain_dataset.py` |
| `09fcff4887ff` | 2,810 | `src/data/transforms.py` |
| `2af539bd47a0` | 923 | `src/losses/segmentation.py` |
| `99d412361445` | 3,228 | `src/training/phase20_selection.py` |
| `1f4e1fd2de7e` | 1,272 | `src/utils/reproducibility.py` |
| `0a38f2338775` | 5,974 | `src/utils/run_lock.py` |
| `7591a8a44715` | 5,991 | `scripts/training/phase21_common.py` |

### Verification harnesses and normative documents — 6
| SHA-256 (12) | Bytes | Path |
|---|---|---|
| `5c8dfd0510d4` | 4,942 | `scripts/verification/c1_build_dependency_lock.py` |
| `1d25ffdc96a0` | 3,743 | `scripts/verification/c1_launch_release_freeze.py` |
| `cc5335d4a7df` | 4,871 | `scripts/verification/c1_launch_release_verify.py` |
| `9ebc1e8a9b5c` | 20,031 | `scripts/verification/c1_synthetic_cuda_verification.py` |
| `b4cdea3ab219` | 19,442 | `reports/planning/c1_launch_release_v1/c1_dependency_lock.json` |
| `57ec4cc27668` | 4,858 | `reports/planning/c1_launch_release_v1/endpoint_clarification_addendum.md` |

## 4. Independent verification

`scripts/verification/c1_launch_release_verify.py` deliberately does **not**
import the launch package. It re-implements canonicalisation and the digest rule
from the published text and re-derives every check:

```
manifest_file_sha256=0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe
release_digest_recomputed=1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1
release_digest_published=1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1
bound_source_count=33
c1_modules_present=8/8
launch_sources_present=4/4
VERIFICATION_PASSED
```

`c1_launch_release_freeze.py --check` also reports `RELEASE_CURRENT`, confirming no
bound file changed after freezing.

## 5. Edits made before the digest, and only those

Per the ordering requirement, all integration-module edits were completed before
the digest was computed:

| File | Change | Backward compatible |
|---|---|---|
| `training_engine.py` | `Trainer.__init__(..., grant=None)`; real contracts require a `LaunchGrant` and call `grant.authorize_trainer(contract)` instead of the always-raising preparation gate | Yes — `grant` defaults to `None`, all synthetic call sites unchanged |
| `train_driver.py` | `run_real(..., grant=None)`; `verify_preparation()` kept as precondition; `scientific_execution_enabled` branch removed (it is a definition flag, not an authorization); loader factory gated by grant | Yes — `approval`/`launch` kwargs retained so legacy dicts raise `ReadinessError`, not `TypeError` |
| `synthetic_fixture.py` | Added `fixture_loaders_workers(seed, epoch)` at train 4 / eval 2 | Yes — additive |

`readiness.py`, `control.py`, `protocol.json` and `package_identities.json` were
**not** touched.

## 6. What the digest does and does not prove

**Proves:** the exact bytes of 33 sources, the frozen protocol, the architecture,
the training recipe and the dependency lock are the ones this report names, and
that a post-freeze edit to any of them is detectable.

**Does not prove:** that anyone authorized the study. The digest is a
*precondition* for approval, not a substitute. It also does not prove the release
is reconstructible from Git alone — see §7.

## 7. Known limitation — Git tracking of bound sources

Seven bound sources are **not tracked by Git** in this repository:

```
src/models/film/__init__.py
src/models/film/global_medfilm.py
src/data/domain_balanced_sampler.py
src/data/multidomain_dataset.py
src/training/phase20_selection.py
src/utils/run_lock.py
scripts/training/phase21_common.py
```

They are bound by **content digest**, so release integrity is preserved and any
edit is detectable. But they are not reconstructible from Git history alone —
only from this working tree plus the manifest.

These files are **pre-existing untracked work**, not authored or modified by this
task, so they were deliberately **not staged** under the commit policy's
"stage exact task-owned paths only" rule. Adding them is a separate, reviewable
action and is recorded here as an open item:

```
RELEASE_NOT_FULLY_GIT_TRACKED
OPEN_ITEM: add the seven release-bound dependencies to version control in a
           separate reviewed commit, then re-freeze the release digest.
```

Until that is done, treat the manifest as the authority for release integrity and
Git as a partial record.
