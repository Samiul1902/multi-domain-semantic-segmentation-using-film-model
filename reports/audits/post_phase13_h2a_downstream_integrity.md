# POST-PHASE-13 H2-A-B2 — Downstream Integrity Audit

- **status: PASS**
- run id: `post_phase13_h2a_downstream_epoch83_native_policy`
- model attribution: Gemini 3.8 Flash Medium

## Bindings

- H2A protocol: `0fafc793b3a814e010e1fdd48f6a2333042985eaef4a44e0382b3991800da96b`
- H2A B1 training evaluation: `7ecd3a04fd6bfa6051afa3bd4536566d61a81287c73f34fb2e4689d0e0587899`
- H2A best.pt: `2e2e8f7909649f50cf7b830aab357d9e14a4b62b71a00fc0efe22aa300ba54c8`
- Part1D helper: `8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284`
- Global cache manifest: `76e1034d2bc7925260af33826fc19565b2d5ef786c612a7ad71f3bde46fb89a8`

## Frozen H2A proposal identity (457 — authoritative)

| table | SHA-256 |
|---|---|
| case proposals (103) | `93ebebf4ede237e408a7398bfe86620e28054950831595c3a24f7d1e0fe6ef9f` |
| proposals (457) | `4004e5b0b38bec11b9f63934be8efea253f20339952ac57ebf5e0b70e47e454f` |
| component coverage (152) | `e93163b2b42eeadf725eb60c3c7e32c90560dc87392b94b3bc8281d045250368` |
| size stratified | `23435283ecdfb963dabd88cb590c6f388ac74ab385ae3c5148a47efd69f1b1cf` |

## Segmentation checkpoints

| model | SHA-256 |
|---|---|
| UNet | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` |
| Attention U-Net | `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3` |
| UNet++ | `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269` |
| DeepLabV3+ | `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad` |

## Comparators

- Phase13 predicted comparator (`phase13_part1d_predicted_region_case_model_metrics.csv`): `53e93982c0235e32…`
- Phase12 oracle comparator (`phase12_clean_v3_oracle_analysis_audit.json`): `7fbf42fb7d177547…`

## Results

- global cache reused: **YES** · global reproduction: **PASS**
- regional crop evaluations: **1828** (expected 1828)
- case-model rows: **412** (expected 412)
- component-model rows: **608** (expected 608)
- model-summary rows: **4** (expected 4)
- proposal count: **457** (unchanged)
- localizer forwards: **0**
- proposal regeneration: **0**
- new global forwards: **0**
- TEST reads: **0** · external TEST reads: **0**

## Reviewer notebook

`notebooks/phasewise/phase_13_predicted_roi_localization/post_phase13_h2a_downstream_analysis.ipynb`

- SHA `97ad366a6a2fb4f34a506829923363fb3700794b285920186f544781d6543fa7`
- 55 cells / 25 code · **0 unexecuted / 0 errors** · SHA stable ×3
- 31 / 31 required sections present
- complete tables untruncated: 4/4 summary · 412/412 case-model · 608/608 component-model

## Cohort labeling

- Hard-Tiny: **15 components**
- Global-empty: **5 frozen images** containing **8 native components** — reported explicitly as
  `GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES`; never as "8 global-empty images"

## B1 checkpoint-state crosscheck limitation

`NONBLOCKING_SECONDARY_INTEGRITY_CHECK_UNAVAILABLE` — B1 status changed: NO ·
scientific result changed: NO · retraining performed: NO

## Adjudication boundary (NOT crossed)

h2a_outcome_declared: false · go_no_go_issued: false ·
regional_mechanism_promoted: false · winner_architecture: false

**next_action: WAIT_FOR_SUPERVISOR_H2A_OUTCOME_ADJUDICATION_AUTHORIZATION**
