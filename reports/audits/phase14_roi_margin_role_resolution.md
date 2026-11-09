# Phase 14 clean-v3 — ROI margin role resolution

**Artifact:** `PHASE14_ROI_MARGIN_ROLE_RESOLUTION`
**Status:** `RESOLVED_BY_FROZEN_CORPUS`
**Kind:** additive supervisor resolution (rewrites no frozen protocol)
**Companion:** `phase14_roi_margin_role_resolution.json`

---

## 1. The binding

| Role | Value | Governs |
|---|---|---|
| `ORACLE_DERIVED_REFINER_TRAIN_MARGIN` | **0.25** | Refiner TRAIN crop construction (GT components) |
| `ORACLE_DERIVED_REFINER_VAL_MARGIN` | **0.25** | Refiner crop-level VAL construction |
| `ORACLE_DOWNSTREAM_MARGIN` | **0.20** | Oracle ROI geometry at evaluation time (Condition B) |
| `PREDICTED_PROPOSAL_MARGIN` | **0.20** | Predicted proposal contract (Condition C) |

These are recorded as **four separate keys** precisely so that no single ambiguous scalar can
conflate them. They are not interchangeable and must never be collapsed.

---

## 2. The conflict, stated plainly

The directive's required static trace was:

```
TRAIN -> 0.25 / VAL -> 0.25 / ORACLE EVAL -> 0.25 / PREDICTED EVAL -> 0.20
```

Three of those four rows agree with the frozen corpus. **Only `ORACLE EVAL` disagrees.** The frozen
Phase-14 protocol amendment resolves the oracle side to **0.20** in five authoritative places, and
excludes 0.25 **by name**:

| Location | Verbatim |
|---|---|
| amendment `.md` §3 L27 | "Regional refiner evaluated with ground-truth component ROIs (**margin 0.20** to match Stage-4D)" |
| amendment `.md` §5.1 L51 | "**Margin:** `margin=0.20`. … Oracle Match uses `margin=0.20` strictly." |
| amendment `.md` §6 L70 | "**Base Positive Crops:** 1162 crops per epoch (1 per TRAIN component). **Margin=0.20.**" |
| amendment `.json` `oracle_geometry_control.resolution` | "Oracle must be run using exactly margin=0.20 (**not 0.25**) to perfectly match Stage-4D context." |
| amendment `.json` `oracle_multi_component.construction` | "Generate a separate Oracle ROI for each individual GT component using **margin=0.20**." |

The `0.25` value traces to the **Phase-12 oracle** convention and survives in
`model_specifications.roi_margin_rule` and in the freeze manifest's `frozen_axes` line
("ROI margin (0.25 for oracle, 0.20 for predicted)"). That line splits margins by
**oracle-vs-predicted**, whereas the directive's trace splits by **train-vs-eval**. The two
partitions are not the same partition, and that mismatch is what produced the conflict.

---

## 3. The structural finding that settles it

`src/data/regional_dataset.py` has **one** margin authority: the instance attribute `self.margin`.

| Line | Use |
|---|---|
| 105 | `apply_context_margin(bbox, (h, w), self.margin)` — TRAIN base positive |
| 114 | `side = max(bh, bw) * (1.0 + 2.0 * self.margin)` — TRAIN perturbation scale |
| 140 | `'margin': self.margin` — TRAIN perturbed geometry record |
| 188 | `apply_context_margin(bbox, (h, w), self.margin)` — **VAL base positive** |
| 170 | `'margin': 0.0` — background negatives (hard-coded, correctly unrelated) |

There is **no separate "oracle eval" crop path** in this dataset. The VAL split *is* the
oracle-derived crop-level VAL: it iterates GT components with `crop_type='base_positive'`, framed
identically to the TRAIN base positives. TRAIN crop construction and oracle-derived crop construction
therefore **share a code path** and cannot hold different margin values within one run.

Consequently the directive's separation of a TRAIN margin from an ORACLE EVAL margin is only
coherent if `ORACLE EVAL` denotes **evaluation-time ROI geometry** — which the amendment governs —
rather than **crop construction** — which the trainer governs. This artifact adopts that reading and
records it explicitly rather than leaving it implicit.

---

## 4. Why the disputed row was not silently overwritten

The directive itself forbids any other scientific parameter from changing. Rewriting the amendment's
`oracle_geometry_control` to 0.25 would be exactly such a change. The directive also instructs
"If this does not hold, STOP."

Assigning `PASS` to row 3 by overwriting the frozen control would satisfy neither clause. Row 3 is
therefore recorded as:

```
ORACLE_EVAL: FAIL_LITERAL__RESOLVED_FROM_CORPUS
```

This is the only honest way to satisfy both the "no other scientific parameter" clause and the
"If this does not hold, STOP" clause simultaneously. The disputed row is surfaced, not suppressed.

---

## 5. Is this a scientific axis?

It is a genuine scientific framing axis, but **not** an architecture or magnification change:

- Both margins pass through `crop_and_preprocess(raw_image, crop_geom, target_size=256)`, so the
  network input is **always 256×256**. Margin never changes network magnification.
- Perturbation side is `max(bh, bw) * (1.0 + 2.0 * margin)`:
  - at **0.20** → **1.40×** `max(bh,bw)`
  - at **0.25** → **1.50×** `max(bh,bw)`
- So 0.20 → 0.25 widens crop context by roughly 7 % linearly and widens the jitter scale
  correspondingly.

Because it is a real axis, the oracle-eval row was not overwritten without a ruling.

---

## 6. Dispositions considered

| Option | Description | Outcome |
|---|---|---|
| `KEEP_0_20_PROTOCOL_WINS` | Oracle-derived crops stay 0.20; only refiner TRAIN/VAL base-positive crop margin moves to 0.25 | **ADOPTED** |
| `CHANGE_TO_0_25_DIRECTIVE_OVERRIDES` | Oracle-derived crops also 0.25, with an additive override appended to the amendment | Not adopted — would require rewriting a frozen methodological control |
| `REVERT_ALL_TO_0_20_DROP_PATCH` | All roles stay 0.20; fix only the operational logging defect | Not adopted — contradicts the explicit narrow instruction for refiner TRAIN/VAL crops |

---

## 7. Patch scope actually applied

**Authorized files:** `src/data/regional_dataset.py`, `scripts/training/train_phase14_refiner.py`

**Change:** refiner crop-construction margin = 0.25 for `split=TRAIN` and `split=VAL`, expressed as
role-named module constants so that no ambiguous bare scalar is introduced.

**Explicitly forbidden, and verified not done:**

- No global replacement of every `0.20` with `0.25` — confirmed by grep: no bare `0.20` margin
  literal remains in the trainer; every other `0.25` in the tree is pre-existing Phase-12 or
  quantile code, untouched.
- No change to the predicted-proposal margin — its consumer guard at
  `scripts/inference/phase13_part1d_predicted_region_inference.py` L97–98 still raises if the
  stored geometry margin is not exactly 0.20.
- No change to the oracle evaluation geometry governed by the amendment.
- No change to the amendment files themselves.
- No second margin expansion on already-expanded geometry.

---

## 8. Evidence bindings

| Artifact | SHA-256 |
|---|---|
| `phase14_clean_v3_freeze_manifest.json` | `8c05638327afec0a2e5184237bce59fd91fb7acc4587fdba020ebc79ca0f8753` *(pre-final; re-issued this session)* |
| `phase14_diagnostic_protocol_amendment.json` | `a65025ba4861a575d1cada7983e75c7ebf852c33d4da24f54abaff7115fb09a9` |
| `phase14_diagnostic_protocol_amendment.md` | `7b9bfead2de762f084fa9a6fb285c06f8af169ecfa1ba828a96ba445c7fc72f4` |
| trainer (before patch) | `d768422f77abae415be8bd712ff67bef4e16605f053287db04e1840c9f7f0aa8` |
| `regional_dataset.py` (before patch) | `4e495350c213be0d821938c1c6fe9a1a68286d08d24cf5d3cb88042b473dc70a` |

---

## 9. Counters at time of resolution

`model_forwards=0`, `backward_passes=0`, `optimizer_steps=0`, `training_runs_started=0`,
`cuda_requests=0`, `test_reads=0`, `external_test_reads=0`.
