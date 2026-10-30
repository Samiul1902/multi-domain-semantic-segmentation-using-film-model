# PHASE 36 v1.1 — EXECUTION SEMANTICS AMENDMENT

**METHOD:** RA-MedFiLM-BARR
**REVISION:** `ra_medfilm_barr_phase36_robustness_v1_1`
**CLASSIFICATION:** `PRE_EXECUTION_PROSPECTIVE_SCIENTIFIC_IMPLEMENTATION_AMENDMENT`

`scientific_execution_started = false`
`protected_data_opened = false`

This document is **additive**. It does **not** alter `docs/phase36_robustness_spec_v1_0.md`
(SHA-256 `abe62cd3ddc2ea22ac7bb4bfe473a3f87399e07b24dc9771283723a18af8d6a8`), which remains
byte-for-byte preserved. It resolves exactly one scientifically load-bearing ambiguity —
**the proposal-perturbation insertion / recomputation contract** — plus the executable
completion of a source that was previously a non-executable skeleton.

The v1.0 pre-construction smoke was **BLOCKED** (see
`reports/audits/phase36_v1_0_preconstruction_smoke_block_record_v1_1.json`) with
zero model constructions, zero checkpoint deserializations, zero forwards, zero autograd,
zero protected-data reads, and zero scientific outputs. No scientific result existed before
this amendment; no protected data was opened before this amendment. The amendment is
therefore **prospective**.

---

## 0. PRESERVED UNCHANGED

The following are carried over **verbatim** from v1.0 and must not be re-interpreted:

| Contract | v1.0 authority |
|---|---|
| Image perturbation registry (13 conditions) | `phase36_robustness_common_v1_0.py` `IMAGE_CONDITIONS` |
| Proposal perturbation registry (7 conditions) | `phase36_robustness_common_v1_0.py` `PROPOSAL_CONDITIONS` |
| Perturbation severities | common module `IMAGE_CONDITIONS` values |
| Noise base seeds `{42, 123, 3407}` | `NOISE_BASE_SEEDS` |
| VAL808 population (n=808) | `POPULATION_N`, manifest `082c80b2...` |
| Metrics (Dice primary, IoU/HD95 secondary) | `src/metrics/evaluation_metrics.py` `6c515f6f...` |
| A8/C9 policy (budget 0.25) | `phase26_exec_common.py`, bundle `f7aebb0f...` |
| Thresholds `0.50` / `0.30` | canonical |
| Figures R1–R5; tables (9, incl. conditional KUB) | `FIGURES`, `TABLES` |
| Claim boundary | `DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE` |
| KUB subgroup reporting rule | reporting-only metadata, never classes/task-ids |

Model checkpoints are **unchanged**: G `286689fd...`, B_phi `8a412b2f...`,
R_psi `6d28608a...`, S_omega `eee9b97b...`.

---

## 1. CLEAN REFERENCE SEMANTICS (§D)

The Phase27 per-sample scores (`70213393...`) and Phase29 routing decisions
(`df4a0f37...`) remain the **historical scalar/routing authority**. They **do not**
contain segmentation masks and are never treated as if they did.

During **future Phase36 SCIENCE**, the run executes:

### STAGE 1 — CLEAN REFERENCE GENERATION AND EQUIVALENCE GATE

For each of the 808 authorized VAL samples:

1. load the original clean image **once**;
2. load GT **once** under Phase36 authorization;
3. execute the complete frozen RA-MedFiLM-BARR clean system;
4. persist:
   - clean G probability map (and logits as needed);
   - clean proposal geometry (canonical ROI030 crop metadata, incl. `crop_side_pixels`,
     `clip_x1`, `clip_y1`, `clip_x2`, `clip_y2`);
   - clean B_phi 202-D vector;
   - clean router score / decision;
   - clean safety state;
   - clean final-source state;
   - **clean final binary segmentation mask**;
   - clean Dice / IoU / HD95;
5. persist the **clean final binary mask** as the sole authority for
   `prediction_consistency_Dice`.

**PROHIBITED reconstruction.** The clean mask must **never** be reconstructed from:
`final_dice`, foreground pixel count, router decision, `final_source`, or any scalar
Phase27/29 field.

The clean mask arises **prospectively inside the same frozen Phase36 science run**, before
any non-clean perturbation.

---

## 2. CLEAN EQUIVALENCE GATE (§E)

Before any perturbation result is produced, the generated CLEAN pass is compared against
the bound clean references. Require exactly:

- `sample-id population = 808`
- task/domain identity exact
- routing decision / final-source compatibility with the bound clean routing authority

Clean final Dice comparison, frozen prospectively per sample:

```
np.isclose(generated_clean_final_dice, phase27_bound_final_dice, atol=1e-7, rtol=0)
```

Route state is compared **exactly** where the historical authority provides it.

Required: `clean_reference_equivalence_all_pass = true`.

If any sample fails: **STOP BEFORE ANY PERTURBATION EXECUTION.** Preserve the failure.
No threshold tuning. No retry.

---

## 3. CLEAN EXECUTION ORDER (§F)

The future science run MUST complete and close the full 808-case CLEAN equivalence gate
**before** executing any non-clean perturbation condition.

```
SOURCE FREEZE
  -> OPEN VAL
    -> CLEAN808 GENERATION
      -> CLEAN808 EQUIVALENCE GATE
        -> ONLY IF PASS:
             IMAGE PERTURBATIONS
             AND PROPOSAL PERTURBATIONS
```

No interleaving of clean-reference validation with outcome inspection.

---

## 4. IMAGE PERTURBATION EXECUTION SEMANTICS (§G)

Every non-clean **image** perturbation starts from the **original clean image**.
For each image-perturbation realization the **complete** frozen system is re-run:

```
perturbed image
  -> complete frozen G
    -> proposal generation
      -> exact Phase25B 202-D feature assembly
        -> B_phi
          -> frozen A8/C9 decision
            -> if EXECUTE: R_psi
              -> S_omega
                -> final routed segmentation
```

All model decisions are **recomputed** for image perturbations.
**No CLEAN G feature reuse** for image perturbations.
Noise realizations use the already-frozen 3-seed rule (§9 below, as amended).

---

## 5. PROPOSAL PERTURBATION INSERTION CONTRACT (§H) — **LOAD-BEARING AMENDMENT**

Proposal perturbations isolate **proposal / localization sensitivity**. For each sample:

1. run/reuse the CLEAN G outputs **exactly once**;
2. derive the canonical proposal from `clean p_global >= 0.30`;
3. derive canonical proposal / crop geometry via
   `RAMedFiLMBARR._roi_window_from_probability(clean_p_global, 0.30, 1.50)`;
4. perturb **only that geometry** according to the frozen proposal registry;
5. **DO NOT rerun G.**

### 5.1 REUSED FROM CLEAN

- the original clean input image;
- G logits / probabilities;
- G global feature maps;
- all quantities the canonical Phase25B implementation defines as **global-only**
  (the three `*_global` 32-D groups and the eight `P`-only scalars = 104 dims).

### 5.2 RECOMPUTED

- every **ROI-dependent feature** using the **perturbed** geometry
  (the three `*_roi` 32-D groups = 96 dims);
- every **geometry/proposal-derived scalar**
  (`predicted_roi_area_fraction` @192.. no, @200, `predicted_roi_side` @201 = 2 dims);
- the **full canonical 202-D B_phi vector** via the exact frozen Phase25B
  `build_feature_vector(cmaps, P, roi_row)` with a perturbed `roi_row`;
- B_phi raw `delta_hat`;
- the A8/C9 resource-aware decision;
- if EXECUTE:
  - R_psi crop / execution using the **perturbed** geometry;
  - post-refinement safety quantities;
  - S_omega;
  - final accept / reject / fusion;
- the final routed segmentation.

### 5.3 FROZEN CONTRACT FLAGS

```
proposal_perturbation_changes_router_input =
  TRUE_WHEN_CANONICAL_202D_EXTRACTOR_HAS_GEOMETRY_DEPENDENT_TERMS   # -> TRUE (98 dims)
B_phi_decision_recomputed              = true
R_psi_crop_uses_perturbed_geometry     = true
S_omega_recomputed_if_execute          = true
G_recomputed_for_proposal_perturbation = false
```

### 5.4 EXECUTABLE-TRUTH RESOLUTION (load-bearing)

The canonical executable (`src/models/barr/ra_medfilm_barr.py`) accepts
`router_features_202` and `roi_window` as **independent** arguments, and
`_roi_window_from_probability` is consumed **only** at the refiner-crop and fusion steps —
**not** by the 202-D extractor. The proposal dependency of the 202-D vector lives in the
**extractor's `roi_row`** (`clip_x1`, `clip_y1`, `clip_x2`, `clip_y2`, `crop_side_pixels`).

Therefore the executable v1.1 contract is frozen as:

> A perturbed proposal geometry feeds **both**
> (a) `build_feature_vector(cmaps, P, perturbed_roi_row)` — reassembling the 202-D vector
> with exactly the 98 geometry-dependent dims recomputed — **and**
> (b) `roi_window = perturbed_window` for the R_psi crop and the fusion window.

No prose contract overrides bound code. The extractor itself is reused **verbatim**; only
its `roi_row` input changes.

**Explicit non-assumption:** we do **not** freeze that B_phi must numerically change. We
freeze only that its **full input is REASSEMBLED** from the exact canonical extractor.

---

## 6. EMPTY CANONICAL PROPOSAL (§J)

If the clean canonical proposal is empty (`_roi_window_from_probability` returns `None`):

- all NON-CLEAN proposal-geometry perturbations are `NOT_APPLICABLE_EMPTY_PROPOSAL`;
- **no** synthetic box; **no** fallback box; **no** outcome-dependent geometry;
- `PROPOSAL_CLEAN` follows the canonical frozen state-machine behaviour;
- N/A proposal conditions are **excluded** from the worst-proposal minimum.

---

## 7. EXACT NOISE-SEED CONVERSION (§Q) — **PROSPECTIVE CLARIFICATION**

The v1.0 common module implemented the seed as
`int.from_bytes(sha256(msg).digest()[:8], "big")` — the **first 8 bytes** (64-bit).
The v1.0 unit artifact asserted that exact behaviour.

**v1.1 supersedes this for all future v1.1 smoke and science**, freezing explicitly:

```python
seed_text = f"phase36|gaussian_noise|{base_seed}|{sample_id}"
digest_hex = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
seed_uint32 = int(digest_hex[:8], 16)          # FIRST EIGHT HEX CHARACTERS
rng = numpy.random.Generator(numpy.random.PCG64(seed_uint32))
```

- `[:8]` means **first eight HEX CHARACTERS**, **not** bytes.
- encoding: **UTF-8**.
- integer base: **16** (hexadecimal).
- integer domain: `0 <= seed_uint32 <= 0xFFFFFFFF`.

The v1.0 module is **not modified** (§A). The v1.1 common module
(`phase36_robustness_common_v1_1.py`) carries this rule and overrides the v1.0 derivation
for all v1.1 execution. Unit, smoke and science for v1.1 use **exactly** this algorithm.
The v1.0→v1.1 difference in derived seeds is a **disclosed prospective change**, not a
correction of a scientific result (no scientific result existed).

---

## 8. METRIC SEMANTICS (§O)

`_confusion` is implemented by **binding** the canonical metric authority rather than
inventing formulas.

- **Dice:** `src/metrics/evaluation_metrics.py::dice` (eps `1e-7`) over
  `binary_confusion_counts`.
- **IoU:** `evaluation_metrics.py::iou` (eps `1e-7`); empty-case behaviour recorded from
  the frozen policy.
- **HD95:** `evaluation_metrics.py::hd95`; empty/undefined → **NaN remains NaN**.

**Empty-case semantics** (from `reports/audits/evaluation_empty_mask_policy.json`,
`16e702fd...`):

| case | Dice | IoU | HD95 |
|---|---|---|---|
| GT empty ∧ pred empty | 1.0 | 1.0 | NaN (both empty) |
| GT empty ∧ pred non-empty | 0.0 | 0.0 | NaN |
| GT non-empty ∧ pred empty | 0.0 | 0.0 | NaN |
| both non-empty | formula | formula | formula |

**HD95 descriptive aggregation** (frozen prospectively):

```
n_total
n_finite
mean    = mean over FINITE values only
median  = median over FINITE values only
n_nan
```

NaN is **never** substituted with 0 or infinity.

---

## 9. VAL808 PATH RESOLUTION (§M)

Manifest-authoritative resolution; identity is **`sample_id`**, which is a **content hash**,
**not** a filename stem. Filename/stem is transport metadata only.

Per row bind: `sample_id`, `dataset/domain`, `task_id`, image path, mask path.

Reject: TEST path, ROUTER_HOLDOUT path, TRAIN path in Phase36 science.
Only VAL808 may enter science.

---

## 10. MASK PREPROCESSING (§N)

Bind the exact canonical pipeline `src/data/transforms.py` (`09fcff48...`):

- image: `L`/`RGB` → aspect-preserving resize (rw, rh) **BILINEAR**, centre `ImageOps.expand` pad to 512×512, `/255.0`
- mask: **NEAREST** resize to (rw, rh), centre `ImageOps.expand` pad, then `(np.asarray(mask) > 0)` → float32

No new GT conversion rule is created. KUB heterogeneous native labels collapse by `>0`.
Kidney / Bladder / Ureteric metadata remain **reporting-only**.

---

## 11. SOURCE FREEZE REQUIREMENT

`future_phase36_smoke_must_use_exact_v1_1_bytes = true`.

The v1.1 execution source must be used byte-exact by the future smoke; any change requires
a new revision and a new freeze.

---

## 12. NO-EXECUTION STATEMENT

This amendment performs **no** model construction, **no** checkpoint load, **no** forward,
**no** autograd, **no** perturbation generation on medical data, and **no** protected-data
access. Phase36 scientific execution remains `NOT_STARTED`. TEST remains
`LOCKED_UNTIL_PHASE39`.
