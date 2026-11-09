# POST-PHASE-13 H2-B-B2 — Downstream Integrity Audit

- status: **PASS**
- run id: `post_phase13_h2b_downstream_best_native_policy`

## Bindings

- H2B protocol: `22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e`
- H2B B1 evaluation: `34a52942ea4ef9da21c4aa450a925c8c59ada771e08f99ab99c3ec669c1e2175`
- H2B best.pt: `a9147ad7d1835a6e4ef8d66cc04c063db85b2f9a65585a4a34ae2acfef05f028`
- H2B loss module: `40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75`
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

- regional crop evaluations: **1952** (expected 1952)
- case-model rows: **412** (expected 412)
- component-model rows: **608** (expected 608)
- model-summary rows: **4** (expected 4)
- localizer forwards: **0**
- proposal regeneration: **0**
- new global forwards: **0**

**next_action: WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION**
