# Phase 20 — Five-Model Conventional Baseline: Final Training Report

**Sequence terminal event:** `PHASE 20B SEQUENCE COMPLETE: all requested models naturally terminated`
at **2026-09-28 11:15:40 (GMT+6)**, after 33h 03m of driver wall time.

**Scope:** Phase 20A (UNet++) + Phase 20B (four conventional architectures), all trained under the
identical frozen Phase-20 protocol.

> **Governance status.** This report covers **training completion only**. All five models closed with
> `EARLY_STOPPING_PATIENCE`. Every model's `closure.json` records
> `independent_duplicate_runs: 0` and `test_reads` = 0 on all four counters. The **five-model
> benchmark freeze has NOT yet been produced** — it still requires the canonical disk-only replay,
> metrics + bootstrap CI, confusion matrices, the 808-row prediction table, KUB subgroups, and the
> paired-bootstrap comparison. Do not cite these five numbers as a frozen benchmark result yet.
>
> Nothing in `reports/audits/phase20_shared_global_baseline_protocol.json`, any
> `phase20b_*_architecture_binding.json`, or any `phase20b_*_pre_execution_check.json` was modified.

## 1. Final standings

Ranked by macro-domain mean VAL Dice at each model's own best epoch.

| rank | model | class | params | best epoch | **macro Dice** | final epoch | stop |
|---|---|---|---|---|---|---|---|
| 1 | **DeepLabV3+** | `DeepLabV3Plus` | 40,347,041 | 57 | **0.827653** | 72 | EARLY_STOPPING_PATIENCE |
| 2 | **Transformer/MiT-style U-Net** | `TransformerMiTUNet` | 16,347,777 | 74 | **0.822381** | 89 | EARLY_STOPPING_PATIENCE |
| 3 | U-Net++ (20A) | `UNetPP` | 9,159,681 | 55 | **0.792007** | 70 | EARLY_STOPPING_PATIENCE |
| 4 | Attention U-Net | `AttentionUNet` | 7,851,285 | 64 | **0.789039** | 79 | EARLY_STOPPING_PATIENCE |
| 5 | U-Net | `UNet` | 7,763,041 | 74 | **0.787833** | 89 | EARLY_STOPPING_PATIENCE |

The field splits into **two clear tiers**:

- **Tier 1 (two-stage approaches):** DeepLabV3+ 0.827653 and Transformer/MiT 0.822381.
- **Tier 2 (classic encoder-decoder):** U-Net++ 0.792007, Attention U-Net 0.789039, U-Net 0.787833.

The gap between the tiers is **~0.030 (3.0 pp)**; the spread *within* tier 2 is only 0.004174
(0.42 pp) — the three U-Net-family variants are statistically indistinguishable on this evidence.

## 2. Per-domain VAL Dice at each model's best epoch

| model | ISIC | BUSI | KVASIR | KUB | macro |
|---|---|---|---|---|---|
| DeepLabV3+ | 0.8853 | **0.8669** | **0.8197** | **0.7388** | **0.827653** |
| Transformer/MiT U-Net | **0.8871** | 0.8640 | 0.8133 | 0.7252 | 0.822381 |
| U-Net++ | 0.8601 | 0.8163 | 0.7710 | 0.7207 | 0.792007 |
| Attention U-Net | 0.8617 | 0.8277 | 0.7710 | 0.6958 | 0.789039 |
| U-Net | 0.8553 | 0.8198 | 0.7552 | 0.7211 | 0.787833 |

### What separates the winner

The top-two margin is only **0.005272 (0.53 pp)** — under a single percentage point. The ordering is
*not* uniform across domains: Transformer/MiT actually leads on **ISIC** (0.8871 vs 0.8853), while
DeepLabV3+ wins on **BUSI, KVASIR, and KUB**. The decisive term is **KVASIR (+0.0064)** and
**KUB (+0.0136)**.

Because the margin is sub-percentage-point, **the paired-bootstrap step is what will determine
whether this ranking is real** rather than run-to-run noise. Treat "DeepLabV3+ > Transformer/MiT"
as provisional until that runs.

### The KUB story

KUB is the hardest domain and has been the project's known bottleneck (tiny objects; TINY-bin Dice
0.531 on the shared baseline). Two patterns stand out:

- **Attention U-Net is the worst on KUB (0.6958)** — attention gates did not relieve the
  tiny-object problem, which is why it ranks below plain U-Net++ despite winning ISIC and BUSI.
- **DeepLabV3+ is the best on KUB (0.7388)** — ASPP multi-scale context appears to genuinely help here.
- KUB recovery trajectories were non-monotonic for several models: DeepLabV3+ went 0.6134 (ep 12) →
  0.7405 (ep 69) → 0.7388 (best ep 57); Transformer/MiT went 0.6946 (ep 42) → 0.7252 (ep 74). Early-epoch
  KUB values are **not** indicative of final KUB performance.

## 3. Training behaviour notes

- **All five terminated by `EARLY_STOPPING_PATIENCE`**, none hit the 100-epoch cap, none diverged.
- **Two models posted late recoveries** rather than clean plateaus: DeepLabV3+ was at bad=12 at ep 51
  before setting its eventual best at ep 57; Transformer/MiT recovered from bad=9-10 to set best at
  ep 74. Reading these curves mid-run would have mispredicted the final ranking.
- **Per-epoch cost** was broadly 400–510 s across all five architectures despite a 5.2× parameter
  range (7.76 M → 40.3 M), i.e. runtime was dominated by data/resolution, not model size.
- **`unet` is the only model with `resume_count: 1`** — a single resume of the *same* logical run after
  an execution-harness teardown. This is recorded in its closure; `independent_duplicate_runs` is 0.
  The other three ran with `resume_count: 0`.
- Wall-clock per model: U-Net 2.26h (resumed portion) / Attention U-Net 10.02h / DeepLabV3+ 9.02h /
  Transformer-MiT 11.76h.

## 4. Provenance and integrity

- Every closure verified binding SHA + pre-execution check SHA at run start; the trainer is
  fail-closed (rc=2) on any drift. No rc=2 abort occurred across the whole 33-hour sequence.
- TEST lock was verified at each model start (`manifests/test.csv` sha256 matches the frozen lock).
- No TEST content was read: all four `test_reads` counters are 0 for all four 20B models.
- Machine-readable snapshot: `reports/tables/phase20b_five_model_comparison.csv`
  (also `phase20b_model_comparison_in_progress.csv` retained as the interim record).
- Closure files:
  - `experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3/closure.json`
  - `experiments/phase20b_shared_unet_fourdomain_seed42_clean_v3/closure.json`
  - `experiments/phase20b_shared_attention_unet_fourdomain_seed42_clean_v3/closure.json`
  - `experiments/phase20b_shared_deeplabv3plus_fourdomain_seed42_clean_v3/closure.json`
  - `experiments/phase20b_shared_transformer_mit_unet_fourdomain_seed42_clean_v3/closure.json`

### Class-naming cautions (carry these forward)

- `deeplabv3plus` — architecture id is `deeplabv3plus_resnet50_os16_random_init_no_pretrained_aspp_rates_6_12_18`.
  It is **random-init, no pretrained backbone**. Never describe it as ImageNet-pretrained.
- `transformer_mit_unet` — source file carries `LOCAL_RANDOM_INIT__NOT_OFFICIAL_PRETRAINED_MIT_B1`.
  MiT-*style*, widths [64,128,320,512] at base_channels=32. **Not** official pretrained MiT-B1.
  No `timm`/`transformers`/`segmentation_models_pytorch`/`einops` dependency.
- `unetpp` — the Phase-20A closure predates the 20B schema and does not carry
  `architecture`/`model_class`/`model_source_file`; class info sourced from `src/models/unetpp.py`.

## 5. Remaining steps to the freeze

Per the frozen Phase-20B plan, the following are **not yet executed**:

1. Closure + disk-only replay (no re-inference).
2. ONE canonical VAL pass per model; metrics + bootstrap CI.
3. Confusion matrices; 808-row VAL prediction table; KUB size-subgroup analysis.
4. The 64 shared VAL gallery cases (reusing the frozen gallery IDs).
5. Per-model notebook artifacts.
6. Five-model comparison + paired-bootstrap significance testing.
7. Emit `reports/audits/phase20_five_model_baseline_benchmark_freeze.json` and the terminal marker
   `PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`.

**Phase 21 remains NOT STARTED.** It stays blocked until the freeze above is produced.
