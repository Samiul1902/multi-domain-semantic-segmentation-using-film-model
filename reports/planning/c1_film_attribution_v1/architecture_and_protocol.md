# C1 FiLM attribution — matched-control specification and prospective protocol

**Study:** C1_FILM_ATTRIBUTION_V1. PROTOCOL_READY_FOR_APPROVAL; AUTHORIZATION_PENDING; SCIENTIFIC_EXECUTION_NOT_STARTED. One preparation package, not a new chain of governance phases. `protocol.json` is the machine-readable design; no approval is implied by freezing prospective choices.

## 1. Verified architecture and exact intervention

Unchanged source `D:\Softfors\jup\src\models\film\global_medfilm.py` (SHA a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f) implements:

- One RGB shared encoder-decoder. Residual Conv3x3/GroupNorm/SiLU blocks; widths 24/48/96/192/256, four MaxPool2d(2) reductions, four bilinear upsample-and-concatenate decoder blocks, one shared 1x1 foreground-logit head. GroupNorm uses first divisor among 8/4/2/1. No dataset-specific head, SE, deep supervision, refiner, router, fusion or distillation.
- `Embedding(4,32)` initialized normal(mean=0,std=0.02), **not zero**. Task IDs are ISIC=0, BUSI=1, KVASIR=2, KUB=3. The only use of task IDs in forward is this embedding (aside from validity checks).
- Five FiLM sites: bridge=256, decoder4=192, decoder3=96, decoder2=48, decoder1=24. Each maps embedding through Linear(32,64), SiLU, Linear(64,2C), split then tanh: gamma=tanh(gamma_raw), beta=tanh(beta_raw), F_hat=(1+gamma)F+beta, broadcast [B,C,1,1].
- Hidden projection weights Xavier-uniform and biases zero; each output projection weight/bias exactly zero. Backbone Conv2d weights Kaiming-normal fan-out/relu, biases zero where present; head normal std=0.01/bias zero. GroupNorm default affine scale one/bias zero. Thus finite gamma/beta are identically zero at initialization despite random embeddings/hidden weights.

**C1-T:** Fresh canonical GlobalMedFiLM; every parameter trainable. **C1-C:** Exact deep copy of that freshly initialized (never trained) treatment state; freeze all `task_embedding.*` and `film_layers.*` parameters. No architecture modules removed, no forward monkeypatch, no trained checkpoint modification. Verify all five output projections stay zero and gamma=beta=0 for all four tasks. Shared backbone updates remain permitted. Task validation still rejects invalid IDs but valid task identity has no effect on output. Synthetic tests compare the full control against a FiLM-site bypass and compare all valid task IDs.

The prospective helper creates arms on CPU under an isolated/restored RNG state. Identical initial state_dict tensors are verified at every seed; no changed model-construction draw order. Before a future real run, persist backbone initialization digest and use identical per-epoch sampling and augmentation seeds for both arms. Early-stop epochs may differ because the same selection rule acts on different training trajectories; do not force the control to the historical best epoch.

Total count should be 3,523,001 in both arms; conditioning 90,768 (embedding 128 + FiLM 90,640), shared non-conditioning 3,432,233. Treatment trainable 3,523,001; control trainable 3,432,233, frozen 90,768. Recalculated test inventory is in the synthetic report, not assumed from the old count. Optimizer: one AdamW group per arm containing only requires_grad=True parameters; lr=1e-4, wd=1e-4. Frozen tensors receive no gradients or optimizer state. Identical total parameters do not imply identical effective training/backward cost. Control retains FiLM forward operations but removes conditioning autograd/updates; no speed-up is claimed.

**Naming:** C1-C is not Phase-28 F1, which removes a refiner input channel. The memorandum's separate “Design F1” means freeze-at-initialization and is not reused as an arm name.

## 2. Hypothesis, endpoint and matching

Scientific question: does learnable task-conditioned GlobalMedFiLM differ from a matched identity-modulation control under one predeclared recipe? Null H0: the paired selected-VAL equal-domain macro Dice difference is zero for the predeclared fixed seed set. Alternative: nonzero (positive supports treatment; negative favors identity). This is a development-selection-consumed protocol, not clinical safety or independent generalization. It speaks only to C1, not BARR C2 or baseline C3/AS-08.

Seeds fixed prospectively: 42,123,3407; six fresh logical runs, no historical treatment reuse as a matched replicate. Arms share each seed's initial backbone weights, sample index stream, augmentation RNG policy and training/scoring operations. Run sequentially T then C for seed42, C then T for seed123, T then C for seed3407; record hardware interruptions and resource observations rather than interpreting order as randomized blocking.

Primary point: for each seed, calculate each domain's mean paired per-image selected-checkpoint Dice difference; mean the four domain means equally; then average the three seed effects equally. Neither pixel-pooled confusion Dice nor a pooled case mean substitutes for this endpoint. Secondary: four domain Dice and four domain IoU contrasts under the same selected checkpoints; descriptive only, with all seeds and domains retained.

## 3. Canonical recipe and selection

Sources: `reports/audits/phase20_shared_global_baseline_protocol.json` (b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c), Phase21 binding/config/trainer and `src/training/phase20_selection.py`. All paths resolve under D:\Softfors\jup. Values are inherited, not outcome-tuned:

RGB_3CH, divide by255, aspect-preserving512 resize and center zero pad; bilinear images/nearest masks, foreground>0. TRAIN-only mirror p=0.5, rotation +/-5 degrees, brightness/contrast +/-0.1; VAL augmentation disabled. BCE/Dice weights0.5/0.5, loss epsilon1e-6. AdamW1e-4, wd1e-4; CosineAnnealingLR T_max100 stepped after train/validation each epoch. Train batch4/eval batch8, accumulation1; train workers4/eval workers2, persistent_workers=False; AMP on CUDA; cudnn deterministic=True/benchmark=False. Domain-balanced replacement sampling draws5,832 indices/epoch; derive_epoch_seed=(base_seed*1000003+epoch*7919) modulo (2^31-1), same streams for both arms.

Selection maximizes mean of four per-domain per-image VAL Dice means. `is_new_best` tolerance1e-12: macro>best+tol improves; tie within tol breaks by val_loss<best_loss-tol; full tie retains earlier checkpoint. Same rule, not same chosen epoch. Maximum100 epochs/run, patience15 reset on improvement. Historical validation loss averages batch losses, not a redesigned sample-weighted loss. Metric helper uses sigmoid(logits)>=0.5, binary targets; per-image Dice=(2tp+1e-7)/(2tp+fp+fn+1e-7), IoU=(tp+1e-7)/(tp+fp+fn+1e-7). Keep identical dtype/AMP scoring in arms, no TTA/morphology/tuning. Primary uses selected epoch's per-image validation records; later canonical scorer values, if different, are separate.

TRAIN5832 counts: ISIC2556/BUSI602/KVASIR696/KUB1978. VAL808: ISIC357/BUSI84/KVASIR87/KUB280. Machine contract pins dataset ID, mapping, version, relative manifest paths and documented byte digests. Preparation tests compare metadata only, never open CSVs/images. Future driver must verify approved manifest bytes/rows and disjointness before loading. No TEST/ROUTER_HOLDOUT/external/quarantine use. A changed dataset/count/digest is protocol drift, not an auto-repair.

## 4. Predeclared statistics and interpretation

Fixed-seed primary uncertainty:10,000 percentile bootstrap draws with numpy Generator PCG64 seed20261027. Resample units independently within domains, retaining treatment/control pairing and identical case draws across all three seed effects. KUB must use verified patient IDs, drawing all images of sampled patients with multiplicity. Non-KUB uses individual cases because patient/source IDs are unavailable; disclose dependence risk. Missing KUB grouping aborts clustered analysis, not silent per-case substitution. Each draw computes per-domain case means, equal-domain macro, then equal-seed average. Report2.5/97.5 percentiles as a **conditional-on-three-fixed-training-seeds, selection-consumed case/cluster sampling interval**; it excludes retraining/model-selection uncertainty and does not establish new-population performance.

Report all three paired seed effects, mean, sample SD(ddof1), range separately. No seed t-test/seed CI or BARR/full-system claim from n=3; three is feasibility, not statistical sufficiency. One primary two-sided contrast; eight domain Dice/IoU secondary outcomes descriptive, no secondary significance claims. CI entirely above0: positive conditional development evidence; below0: negative; crossing/touching0: inconclusive. No equivalence, non-inferiority, clinical importance or patient-safety inference. All conclusions retain VAL-selection and fixed-seed caveats.

Retain all six runs/epochs/failures and paired records. Join sample_id one-to-one with domain/group consistency; abort on duplicates/missing/NaN. Missing/incomplete arm/seed blocks the primary claim; never average favorable completed runs, exclude cases by Dice or choose best seed.

## 5. Failure, recovery, compute and scope limits

Maximum six logical runs x100 completed epochs, cumulative96 active GPU-hours: a prospective administrative cap, not a runtime estimate. STOP on OOM/nonfinite loss, device/clock/storage failure, identity violation or scope/digest mismatch. No smaller batch, loss/LR change, silent skipped batch or retry for score. Interrupted runs may resume same ID/arm/seed only after recovery review. Require consistent model/optimizer/scheduler/scaler/epoch/patience/history and RNG/sampler states, control revalidation, epoch draw replay and failure log. A failed pair may remain incomplete; no primary claim until all six complete under approved rules.

Historical source writes history then direct `torch.save` checkpoints; it does **not** establish atomic multi-file commit or persist every RNG state. Its bit-exact resume prose exceeds what these operations alone prove. Before a future launch, the additive C1 real-data driver must synthetically verify same-directory temporary-write/replace, consistent state recovery, RNG/data-order replay and per-arm isolated directories. Do not run the historical trainer against its hard-coded historical paths for C1.

Prospective outputs only `experiments/c1_film_attribution_v1/` and `checkpoints/c1_film_attribution_v1/` with seed/arm directories; neither output tree was created by this task. No real-data driver is included. Current implementation readiness covers matched-control construction, optimizer groups, scope contracts and preparation-only launch refusal. A metadata check does not police someone else's unguarded script. Loader/driver integration, recovery tests, C1 approval and separate launch remain requirements. Overall study is **not execution-ready**.

## 6. Approval and frozen-authority boundary

`package_identities.json` binds this package and source identities; it is not an authorization artifact. Seeds, recipe, statistics and failure decisions are prospective before C1 outcomes. The authority must accept/reject these choices; any amendment must be explicit, versioned and pre-outcome, not an edit to historical records. No new cryptographic trust infrastructure is introduced. Institutional scientific approval and a separate launch work order must name C1 scope/arms/seeds/datasets/analysis/output/resource/executable identities. BARR-M1 approval cannot authorize C1 and is currently absent. A synthetic approval dict cannot activate this preparation build.

## 7. Verification boundaries

`synthetic_test_report.md`/`.json` record CPU-only tests on fabricated tensors and contract metadata, never TRAIN/VAL files or protected data. Source inspection and file hashes are not new segmentation evaluation. `compute_feasibility.md` distinguishes historical timing, static byte arithmetic and current resource metadata from any future runtime benchmark. Status: IMPLEMENTATION_READY for control primitives; PROTOCOL_READY_FOR_APPROVAL; AUTHORIZATION_PENDING; SCIENTIFIC_EXECUTION_NOT_STARTED; real-data driver/recovery integration not delivered or authorized.
