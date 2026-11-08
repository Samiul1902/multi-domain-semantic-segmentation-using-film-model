# Pending Controlled Experiments (C1 / C2 / C3)

**Status:** none of these experiments has been executed. This document records
what exists, what is missing, and what must happen before each can run.

Nothing here is a result. Nothing here was launched during the notebook
reconstruction.

---

## C1 — Learned FiLM versus identity FiLM (attribution)

| | |
|---|---|
| Hypothesis | The learned task-conditioned FiLM modulation contributes measurably to segmentation quality, beyond the identity transform |
| Design | 6 matched runs: C1-T (learned FiLM) and C1-C (identity FiLM) × seeds 42/123/3407 |
| Population | TRAIN5832 optimisation, VAL808 checkpoint selection |
| Estimand | seed-average paired macro-domain Dice (T − C) |
| Status | **0 / 6 runs executed** |
| Implementation | `src/research/c1_film/`, `src/models/film/global_medfilm.py` |
| Protocol | `reports/planning/c1_film_attribution_v1/protocol.json` — SHA-256 `531e3eb2…087a61` |
| Blocker | `C1_RC4_TRUST_ROOT_MISSING`; protocol status `PROTOCOL_READY_FOR_APPROVAL__NOT_APPROVED`, `scientific_execution_enabled = false` |

**Critical caveat.** Freezing a component never reduces the *total* parameter
count. C1-T and C1-C are `deepcopy`-matched, so both have 3,523,001 parameters;
only the trainable count differs (3,523,001 vs 3,432,233, Δ 90,768). Any claim of
a total-parameter difference would be wrong.

**What must happen**

1. Institutional approval of the protocol, or a formal switch to `DECISION_R`
   with a personal licence/ethics attestation.
2. `scientific_execution_enabled = true` in the protocol.
3. RC4 trust root provisioned (`%ProgramData%\InstitutionalC1TrustRC4`), or an
   approved `DECISION_R` release.
4. A reviewed production launcher around `launch_driver_rc4.launch(...)`.

Reference: `docs/publication_readiness/` (authorization, policy, run order).

---

## C2 — Controlled causal component attribution

| | |
|---|---|
| Hypothesis | Each of R_psi, B_phi and S_omega contributes causally to the FULL system |
| Design | one-factor matched contrasts under a fixed compute budget |
| Population | ROUTER_DEVELOPMENT 4,957 (K = 1,239 routed) |
| Status | **not established** |
| Existing evidence | 13-arm ablation (Phase 28) — *not* a causal ablation |

**Why the existing ablation is not causal**

* A1 → A6/A7 changes routing *and* budget simultaneously.
* A1 → A8 is fully confounded.
* Only **A8 vs A7** is pre-specified and matched — and its 95 % CI **includes
  zero**: `+1.57e-05 [−1.4e-05, +5.1e-05]`.
* All of it is **in-sample** on the development population.

**What must happen:** a pre-registered one-factor design with matched compute,
executed out-of-sample. Not a re-analysis of the existing arms.

---

## C3 — Eight-model × three-seed benchmark

| | |
|---|---|
| Hypothesis | ReMedFiLM FULL beats conventional baselines under an identical protocol |
| Design | 8 models × 3 seeds = 24 cells |
| Population | TRAIN5832 / VAL808 |
| Status | **0 / 24 cells executed** |
| Entry point | `scripts/analysis/stage6_eight_model.py baseline-run` |

**Known surface defects (not fixed, disclosed)**

* `stage6_eight_model.py baseline-run` exposes **no** `--device` or `--execute`.
* `baseline_real.py` is a library, so `python -m baseline_real` exits 0 silently
  without doing anything.
* A silent no-op exit 0 must never be read as a completed cell.

**What must happen:** a launcher that actually drives training, per-cell
write-once result artifacts, and an explicit "cell executed" assertion.

---

## What the notebooks do instead

| Notebook | Handling |
|---|---|
| `02_ReMedFiLM_Component_Training` | reports the real component runs; states assembly ≠ joint training |
| `07_ReMedFiLM_Progression_and_Ablation` | reports the 13 arms as development evidence; preserves the null A8-vs-A7 |
| `09_ReMedFiLM_Statistics_and_Reproducibility` | discloses the shared backbone; computes no p-values |
| `11_ReMedFiLM_Accuracy_Compute` | corrects the compute and Dice values |
| Master §17 | lists C1/C2/C3 as `NOT_ESTABLISHED` |

---

## Non-negotiable rules

1. Synthetic tests are **not** a substitute for any of these experiments.
2. A checkpoint's existence is not evidence that its experiment completed.
3. No p-value may be computed on three downstream seeds sharing one backbone.
4. No C1/C2/C3 run may be launched without the authorization above.
5. If authorization is unavailable, the honest terminal state is
   `REMEDFILM_NOTEBOOK_RECONSTRUCTION_PARTIAL__EVIDENCE_GAPS_DISCLOSED` — which is
   what this deliverable reports.
