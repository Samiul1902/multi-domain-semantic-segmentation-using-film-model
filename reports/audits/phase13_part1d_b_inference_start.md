# PHASE-13 PART-1D-B — INFERENCE START AUDIT

- status: **`PART1D_B_INFERENCE_START_AUDIT`**
- run id: `phase13_part1d_b_predicted_region_clean_v3`
- created (UTC): `2026-09-22T04:27:00Z`
- authorization: `SUPERVISOR_AUTHORIZED_PART1D_B_FOUR_MODEL_PREDICTED_REGION_INFERENCE`

## Bindings verified physically before CUDA

| binding | SHA-256 | verified |
|---|---|---|
| R1 protocol | `9089b948ef7563252963bf68d0e0b57a9e891c5e913f54a315bce94c98207eb8` | **PASS** (`SUPERVISOR_FROZEN_PART1D_R1_READY_FOR_INFERENCE`) |
| gate criteria | `342a8bcac2c87bf0b85f7bbd963179e74f029825c0434cf527fbd939d2d13c21` | **PASS** (inspected `NO`, thresholds `0`, state `NOT_DECIDED`, not edited) |
| Part-1D helper | `8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284` | **PASS** |
| Phase-12 case metrics | `080f158fb8b3e3552ac7854c6d9a116e11564bcefa9efdcdbb3511dba090b436` | **PASS** |
| Phase-12 component metrics | `d66933a3c2821d3ab9375eadb5c0540fea145edcf49b648064fe9aa4c460c753` | **PASS** |
| Phase-12 geometry | `29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0` | **PASS** |
| Part-1C case table | `d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed` | **PASS** |
| Part-1C proposals | `8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a` | **PASS** |
| Part-1C component coverage | `2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87` | **PASS** |

### Four frozen segmentation checkpoints

| model | SHA-256 | historical best epoch |
|---|---|---|
| unet | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` | 44 |
| attention_unet | `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3` | 54 |
| unetpp | `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269` | 70 |
| deeplabv3plus | `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad` | 52 |

Reference model **NONE** · winner **NONE** · ranking **NONE**.

## Manifest / taxonomy / population

- manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1` · ROI **EXCLUDED** · TEST **LOCKED**
- VAL FULL_FIELD **103** cases · native components **152** · strata TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16
- frozen proposals **494** (492 interior + **2** bottom-padded) · margin **0.20 already applied** · no second margin
- localizer rerun **FORBIDDEN** · proposal geometry mutation **FORBIDDEN**

## Device

| item | value |
|---|---|
| torch | 2.6.0+cu124 |
| CUDA available | **True** (12.4) |
| device | **NVIDIA GeForce RTX 3060 Ti** (capability 8.6) |
| CPU fallback | **FORBIDDEN** (`require_cuda=True`) |

## Frozen semantics

```
P(x) = R(x)   if U_pred(x)
     = G(x)   otherwise
```

- inside support **REGIONAL REPLACEMENT** · outside **GLOBAL_RETAINED** · overlap **MAX among regional crops only**
- `max(G,R)` inside support **FORBIDDEN** · threshold **0.5 AFTER complete native fusion**
- zero-proposal image → `P = G` exactly
- global reproduction tolerance (max abs case Dice) **1e-4**

### Retention definitions

`D_G` GLOBAL mean Dice · `D_O` ORACLE mean Dice · `D_P` PREDICTED mean Dice
`DELTA_ORACLE_DICE = D_O - D_G` · `DELTA_PRED_DICE = D_P - D_G`
`RETENTION_DICE = (D_P - D_G)/(D_O - D_G)` only when denominator > 0 — **never clipped**;
negative / 0..1 / >1 preserved · `ORACLE_GAP_DICE = D_P - D_O`
IoU / object-recall / FN-reduction gain retention with `N/A` on invalid denominator
(**never a fabricated zero**) · label `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`.

### Case improvement tolerance (numerical equality only — NOT a gate threshold)

improved `> +1e-12` · unchanged `<= 1e-12` · worsened `< -1e-12`

## Run-specific global cache (authorized)

`data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512/<model>/<sample_id>.npy`
— FLOAT32 512-space global probability maps, uint8 probability **FORBIDDEN**, per-item manifest
bindings `model · sample_id · checkpoint_sha · shape · dtype · file_sha`.
Classification: **derived Part-1D-B inference artifact, not a new scientific input**.
The historical 106-case v2 cache is **NOT** reused.

## Not authorized in this part

training · optimizer creation · localizer inference · proposal regeneration · proposal tuning ·
20-config grid · oracle rerun · gate verdict · GO · REVISE_LOCALIZER · NO_GO · Phase 14 ·
TEST content access

## Counters at start

training **0** · optimizer **0** · localizer forwards **0** · proposal generation **0** ·
grid configs **0** · oracle reruns **0** · TEST reads **0** · gate verdict **NOT_DECIDED**

**next_action: `RUN_STAGE_G_GLOBAL_NATIVE_REPRODUCTION_ALL_FOUR_MODELS`**
