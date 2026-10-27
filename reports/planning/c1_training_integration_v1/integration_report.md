# C1 training integration and recovery validation v1

**IMPLEMENTATION_INTEGRATED_SYNTHETIC_VERIFIED / AUTHORIZATION_PENDING / NO_REAL_DATA_EXECUTION.** This engineering package preserves `c1_film_attribution_v1/protocol.json` (SHA531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61), Phase21 sources, earlier package/checkpoints and RC1. The old package's no-driver statement describes its preserved release, not this additive integration.

## Components

- `src/research/c1_film/integration_contract.py`: verifies original package digest, bound files/sources and protocol; exact arm/seed/recipe/dataset/device/runtime/source identity refuses mutations. Synthetic runs have separate mode/miniature shape/count/worker contract and are never canonical scientific runs.
- `training_engine.py`: unchanged matched-arm builder, BCEDiceLoss, Phase21 per-image scoring, Phase20 selection and deterministic epoch-seed policy. Matched optimizer/scheduler/loss/threshold, accurate parameter counts, complete history and selected state. No synthetic Dice values are published as research results.
- `recovery_store.py`: immutable uniquely named epoch payload via same-directory temporary file, flush/fsync and os.replace; SHA-bound latest.json atomic replacement is the commit point. Payload contains current/best model, AdamW/cosine/scaler, all history, selected records, Python/NumPy/torch CPU/CUDA RNG, loader/sampler generators, initialization digest/counts and run contract.
- `synthetic_fixture.py`: fabricated tensor-only TRAIN/VAL fixtures,8 cases each at32x32, same task mapping. Exercises Python/NumPy/torch RNG and seeded domain-balanced sampler; no CSV/images.
- `train_driver.py`: C1-T/C1-C synthetic CLI and real adapter body wired to canonical dataset/preprocessing/loaders and engine. Every real entry, including direct adapter and scientific Trainer construction, refuses through the preserved gate before data/outputs/models. Protocol execution flag stays false; a plain approval dictionary cannot activate this release.
- `.clinerules/01-git-commit-and-push-policy.md`: additive supported Cline workspace rule; no other rule overwritten. Task-owned exact staging only, integrity/confidentiality checks, scoped commit and verified approved upstream push; absent remote means BLOCKED.

## Matching and source semantics

C1-T and C1-C start from identical fresh tensors; C1-C freezes task_embedding/film_layers only. Recomputed totals3,523,001 both; trainable T3,523,001/C3,432,233; control frozen90,768. All valid task IDs produce identity modulation; treatment projection weights can learn. One AdamW group over trainable tensors, lr/wd1e-4, cosine T_max100, canonical BCE/Dice0.5/0.5 epsilon1e-6 and rule-defined validation selection. Synthetic fixture size/epoch/workers are explicitly different; no real recipe was silently changed.

Real adapter body verifies requested TRAIN/VAL path/digest/count/task identity and sample-ID disjointness, with original RGB512 transforms/augmentation and balanced sampling. It is integrated but not exercised on real manifests. Later launch must additionally establish actual patient/source disjointness, allowed image/mask roots and cohort eligibility; counts alone are insufficient. No patient/TEST/HOLDOUT content was inspected here.

## Recovery semantics

Epoch is the durable unit. Before pointer replacement the previous checkpoint stays authoritative; orphan files are ignored, not new replicates. After pointer replacement the new complete epoch is authoritative even if lifecycle completion was interrupted. Resume validates contract and replays contiguous selection history; restores model/optimizer/scheduler/scaler/RNG; reconstructs next-epoch augmentation and loader/sampler streams from frozen seed/epoch policy. It does not resume mid-epoch worker state.

lifecycle.json records RUNNING/PAUSED/COMPLETE. Existing attempt cannot silently start fresh. If no first epoch was committed, resume refuses and requires review; it does not manufacture a checkpoint or independent replicate. Corrupt committed payload/pointer or identity mismatch refuses without older-checkpoint fallback. weights_only=True loads locally produced SHA-checked synthetic payloads; digests detect accidental corruption, not malicious coordinated changes.

Exclusive O_CREAT|O_EXCL writer file blocks concurrency. Explicit stale recovery requires same host/proven-dead positive PID; active/foreign/corrupt/unknown writers refuse. No age override reclaims live writers. This assumes exclusive local storage, not a distributed lock service.

## Scientific launch boundary and limits

Scientific launch is intentionally impossible in this release. The actual C1 approval and separate launch instruction, reliable clock, reserved resources and authenticated institutional scope remain absent. BARR-M1 approval cannot authorize C1. The preserved gate's historical NO_REAL_DATA_DRIVER error name is unchanged: it remains a preparation-only stop even though an unreachable adapter now exists. Activation needs a separately reviewed authorization integration; a CLI flag or local approval-shaped dictionary is insufficient.

CPU epoch equivalence and transaction interruption are tested, not sudden power loss, network filesystem behavior, multi-worker/CUDA replay or cross-runtime migration. File fsync alone does not guarantee physical Windows directory-entry durability. The engine stores per-run active time; the protocol's aggregate six-run96 active-hour cap still needs an approved coordinator, including accounting for work lost before checkpoint commit. Immutable epoch retention avoids automatically deleting history; reserve storage and stop on insufficient capacity. Frozen sources exist hash-bound locally, but several are untracked historical files, so this is not a complete fresh-clone scientific release.

## Verification and Git scope

Final validation: **34 tests plus23 subtests passed**, zero failures/errors/skips,57 JUnit entries; observed suite elapsed27.984 seconds. One added mid-epoch fixture initially failed because a list was substituted for the loader; failure injection was corrected to occur after the real synthetic scaler/optimizer step, and the entire suite reran cleanly. Only targeted synthetic modules run, with CUDA hidden and bytecode/cache writes disabled. Synthetic checkpoints live in external temporary directories, not the scientific output roots. Tests compare bitwise model and optimizer states, not publish synthetic Dice values. `synthetic_validation.json` lists exact tests/counts/failures; `compute_feasibility.md` distinguishes resource metadata and estimates. `integration_identities.json` binds new artifact and old dependency hashes; it is not an approval record.

Git baseline: master at a73fcdcd4dc0b84af3b12f8f746e1a17c4443da6, empty index,40 tracked modifications/deletions. Preservation baseline covers125 old records/files; no existing scientific source or C1 v1 package is edited. New rule and additive integration/test/report files only are intended for this commit. No remote exists: **GIT_REMOTE_CONFIGURATION_REQUIRED / GIT_PUSH_STATUS: BLOCKED**. Initial history contains tracked dataset manifests requiring release review before any upload; no protected content was opened to perform this engineering task.

The active post-commit hook launches an opaque Qoder worker. The operator explicitly permitted a command-local empty hooks directory for this task's commit. Hook bytes and persistent Git configuration stay unchanged; this is not a standing permission to bypass future checks silently.

## Readiness disposition

IMPLEMENTATION_INTEGRATED_SYNTHETIC_VERIFIED: C1-T/C1-C training/recovery core and blocked adapter. PROTOCOL_READY_FOR_APPROVAL: unchanged scientific design. AUTHORIZATION_PENDING: yes. SCIENTIFIC_EXECUTION_NOT_STARTED: yes. OVERALL_SCIENTIFIC_LAUNCH_READY: no. No real manifests/pixels/checkpoints/protected populations were accessed and no real-data performance or experimental result is reported.
