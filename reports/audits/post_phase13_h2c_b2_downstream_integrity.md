# POST-PHASE-13 H2-C-B2 — Downstream Integrity Audit

- status: **PASS**
- run id: `post_phase13_h2c_downstream_best_native_policy`

## Bindings

- H2C protocol: `91166259c10a84e9526eda43e83b227cc760a37b8834a4d4a65fe3e5a90ba4b6`
- H2C B1 evaluation: `ae20f39de080d60f59fbfef93ff42bc0fdebf9f4410149440b06873f1c6f975b`
- H2C best.pt: `021ab63f2cbc064b5c4de90c5f181ebee75f8d10e7dead2eb53f4f9578060f98`
- H2C frozen head module: `666aabcb58572f6c0892302cb6ff1617b3b19f642dc37a688c84943cc1c66e70`
- H2C objective module (H2A focal, retained): `57bf8a0844c12ef9c27a1d170619233b950698ec938f37fef356710dc6c67cb5`
- Part1D helper: `8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284`
- Global cache manifest: `76e1034d2bc7925260af33826fc19565b2d5ef786c612a7ad71f3bde46fb89a8`

## Segmentation checkpoints

| model | SHA-256 |
|---|---|
| UNet | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` |
| Attention U-Net | `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3` |
| UNet++ | `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269` |
| DeepLabV3+ | `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad` |

## Results

- regional crop evaluations: **1848** (expected 1848)
- case-model rows: **412** (expected 412)
- component-model rows: **608** (expected 608)
- model-summary rows: **4** (expected 4)
- localizer forwards: **0**
- proposal regeneration: **0**
- new global forwards: **0**

**next_action: WAIT_FOR_SUPERVISOR_H2C_OUTCOME_ADJUDICATION_AUTHORIZATION**
