# POST-PHASE13 H2A-B2 — Quantitative Reporting Reconciliation

- **Status: PASS**
- **Classification: `CHAT_TRANSCRIPTION_ONLY`**
- Scope: quantitative reporting reconciliation **only**
- Scientific adjudication performed: **NO** · Inference/training performed: **NO**

---

## 1. Finding

The returned **H2A-B2 chat final note** contained quantitative values that **contradict** the
authoritative persisted model summary. In two cases the reported sign was **inverted**, and in one
case a magnitude was reported that matches **no persisted column**. The authoritative on-disk tables,
frozen audits and reviewer notebook were **always correct** — the defect existed only in the chat
transcript and in two mutable continuity documents that had inherited the chat text.

## 2. Artifact bindings (SHA-256, read from disk)

| artifact | SHA-256 |
|---|---|
| `reports/tables/post_phase13_h2a_downstream_model_summary.csv` | `60c707519b3ade980abdc6d7c2f1e71645bb5f5fc89ed32329ec0c642a550677` |
| `reports/tables/post_phase13_h2a_downstream_cross_architecture_summary.csv` | `32de3a43e907af11e07634de5ba80adeda21e63dcf3d71b1ceefdb65ede7dfd8` |
| `reports/audits/post_phase13_h2a_downstream_integrity.json` | `c80a5b7db16013efe1dc74d42d06a26bb5b3f4003ead8564cb4bcdb0efa4bd4b` |
| `notebooks/phasewise/phase_13_predicted_roi_localization/post_phase13_h2a_downstream_analysis.ipynb` | `97ad366a6a2fb4f34a506829923363fb3700794b285920186f544781d6543fa7` |
| `reports/tables/post_phase13_h2a_downstream_case_model_metrics.csv` | `02f9ac5b420015599127e0d51a03dbd2c6f795fa31b877e4f2cde0950ca8f0a0` |
| `reports/tables/post_phase13_h2a_downstream_component_model_metrics.csv` | `b1a35888c259e55af9fe066d49d5ff740b1ce4bc6ec031815fb6971f0b03fd37` |

**Binding clarification (explicitly recorded).** `post_phase13_h2a_downstream_integrity.json` is the
**downstream integrity audit SHA**, and it is **not** a proposal-table SHA. The authoritative
proposal-table SHA lives *inside* that JSON under `proposal_table_shas.proposals`:

| quantity | SHA-256 |
|---|---|
| **proposal table (authoritative)** | `4004e5b0b38bec11b9f63934be8efea253f20339952ac57ebf5e0b70e47e454f` |
| case proposal table | `93ebebf4ede237e408a7398bfe86620e28054950831595c3a24f7d1e0fe6ef9f` |
| component proposal table | `e93163b2b42eeadf725eb60c3c7e32c90560dc87392b94b3bc8281d045250368` |
| stratified proposal table | `23435283ecdfb963dabd88cb590c6f388ac74ab385ae3c5148a47efd69f1b1cf` |

## 3. Authoritative model summary (recomputed from the model summary only)

| model | GLOBAL | Phase13 Pred | H2A Pred | ORACLE | **H2A−GLOBAL** | **H2A−P13** | Retention | ΔFP vs GLOBAL | recov/loss vs GLOBAL |
|---|---|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.302314 | 0.313779 | 0.724722 | **−0.280400** | **+0.011466** | −2.1480 | **+7047.000000** | 17/0 |
| Attention U-Net | 0.629805 | 0.308619 | 0.320173 | 0.699595 | **−0.309632** | **+0.011554** | −4.4367 | **+7306.126214** | 11/0 |
| UNet++ | 0.640516 | 0.311355 | 0.323046 | 0.726679 | **−0.317470** | **+0.011691** | −3.6845 | **+7721.980583** | 14/0 |
| DeepLabV3+ | 0.560251 | 0.277292 | 0.288917 | 0.750372 | **−0.271334** | **+0.011625** | −1.4272 | **+8135.572816** | 17/1 |

## 4. Stale values (chat only — NOT in the authoritative tables)

| quantity | pasted chat value | authoritative value | defect class |
|---|---|---|---|
| `DELTA_H2A_GLOBAL_DICE` | **+0.019465 · +0.011554 · +0.012691 · +0.011625** (positive) | **−0.280400 · −0.309632 · −0.317470 · −0.271334** (negative) | `SIGN_AND_MAGNITUDE_TRANSCRIPTION` |
| `fp_delta_vs_global` | **+1064.8** | **+7047.0 · +7306.126214 · +7721.980583 · +8135.572816** | `MAGNITUDE_TRANSCRIPTION` |

Note on the first defect: the pasted chat numbers for `H2A−GLOBAL` are numerically equal to the
**`H2A−Phase13`** deltas, i.e. the wrong column's values were reported under the wrong heading with
the sign dropped. The `H2A−Phase13` column as reported (`+0.011466 · +0.011554 · +0.011691 ·
+0.011625`) was **correct** and is **not** a defect.

Note on the second defect: `+1064.8` matches **no** persisted column. The nearest persisted quantity
is `fp_delta_vs_phase13`, which is **negative** (−277.97 / −221.94 / −202.51 / −198.84).

## 5. Authoritative cross-architecture summary

| quantity | value |
|---|---|
| cases improved vs GLOBAL (all 4 models) | **3** |
| cases non-worse vs GLOBAL (all 4) | **3** |
| cases worse vs GLOBAL (all 4) | **83** |
| cases improved vs Phase13 (all 4) | **37** |
| cases worse vs Phase13 (all 4) | **38** |
| components recovered vs GLOBAL (≥1 model) | **29** |
| components recovered vs GLOBAL (all 4) | **5** |
| components lost vs GLOBAL (≥1 model) | **1** |
| components lost vs GLOBAL (all 4) | **0** |

## 6. Stale-value search across persisted artifacts

- searched: `reports/audits/`, `reports/tables/`, `reports/**/*.md`, `reports/**/*.json`,
  `docs/TASKS.md`, `docs/MEMORY.md`, `.workbuddy-ai/memory/`
- stale values found in **authoritative tables**: **NO**
- stale values found in **frozen audits**: **NO**
- stale values found in the **reviewer notebook**: **NO**
- stale values found in **mutable continuity docs**: **YES** →
  - `docs/TASKS.md` — the H2A-B2 model-summary table previously carried
    `+0.019465 / +0.011554 / +0.012691 / +0.011625` in the `H2A-Global` column.
    **Corrected in place** to `-0.280400 / -0.309632 / -0.317470 / -0.271334`, and the observation
    bullets rewritten to *"substantially lower than GLOBAL … (−0.271 to −0.317)"* and
    *"higher than Phase13 predicted … (+0.011 to +0.012)"*.
  - `docs/MEMORY.md` — the "Model summary" paragraph previously read
    *"H2A predicted-region Dice improves over GLOBAL for all 4 models (+0.011 to +0.019)"*.
    **Corrected in place.**
- persisted H2A final-note artifact: **does not exist**

## 7. Repair policy applied

- authoritative tables modified: **NO**
- frozen audits rewritten: **NO**
- mutable continuity docs corrected: **YES** (`docs/TASKS.md`, `docs/MEMORY.md`)
- artifacts created: this JSON + this MD
- scientific result changed: **NO**
- B2 execution status changed: **NO**
- H2A outcome adjudicated: **NO**

## 8. Preserved valid evidence (descriptive, unadjudicated)

- H2A predicted-region macro Dice is **below GLOBAL for all four** architectures (−0.271 to −0.317)
  and **above Phase13 predicted for all four** (+0.011 to +0.012); it also remains far below ORACLE.
- `H2A_ORACLE_BENEFIT_RETENTION` is **negative for all four** architectures.
- `fp_delta_vs_global` is **large and positive for all four** (+7047 to +8136).
- component losses vs GLOBAL are **0 for three of four**, and **1 for DeepLabV3+**.
- 457 frozen proposals (no regeneration), 1828 regional crop evaluations, **0** localizer forwards,
  **0** new global forwards, global cache reused (412/412 reproduced), **0** TEST reads.

next_action: `WAIT_FOR_SUPERVISOR_H2A_OUTCOME_ADJUDICATION_AUTHORIZATION`
