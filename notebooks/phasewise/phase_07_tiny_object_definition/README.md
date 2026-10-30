# Phase 07 — Tiny-Object Definition (`phase_07_tiny_object_definition`)

## Phase-07 status

| Part | Scope | Status | Notebook SHA |
|---|---|---|---|
| **1A** | Historical-definition audit + TRAIN-only candidate design | COMPLETE — **candidates NOT FROZEN** | `f2ff7969d4c446c5c7fa737c7cbf36925123c97db1ca86593dbddea842a31eb9` |
| **1B** | Canonical CLEAN-v3 taxonomy **FREEZE** + post-freeze VAL characterization | COMPLETE — **FROZEN** | `c00eb062837c7adf27011a8450dfd30600576b2ff4e091bf00b1ebd2078c4d78` |

**Part 1A** designed and compared exploratory candidates; nothing was frozen.
**Part 1B** froze the supervisor-selected design as `kub_size_clean_v3_v1`, re-deriving
the numerical quartiles from CLEAN-v3 TRAIN, then characterized VAL **after** the freeze.

- **Active development manifest:** `phase4_v3`
- **Historical manifest:** `phase4_v2`
- **TEST medical content:** never accessed (0 reads / 0 visualizations / 0 metrics)

---

# Part 1B — FROZEN Taxonomy

## 1. Frozen design — `kub_size_clean_v3_v1`

| Field | Value |
|---|---|
| Taxonomy ID | `kub_size_clean_v3_v1` |
| Status | **FROZEN** |
| Unit | object (connected foreground component) |
| Connectivity | **8** |
| Foreground rule | `mask > 0` |
| Acquisition scope | **FULL_FIELD** |
| ROI handling | `ROI_NOT_PRIMARY_BINNED` |
| Metric | `component_ratio` = component_pixels / (native_h × native_w) |
| Coordinate system | native mask geometry normalized by native full-image area |

| Quartile | FROZEN value |
|---|---|
| Q25 | `0.0001497998649691358` |
| Q50 | `0.0003401438395182292` |
| Q75 | `0.0008279682677469136` |

Boundary semantics: TINY `x ≤ Q25`; SMALL `Q25 < x ≤ Q50`; MEDIUM `Q50 < x ≤ Q75`;
LARGE `x > Q75`. No rounding before classification; boundary values fall to the **lower** bin.

## 2. Historical taxonomy — `kub_size_v1` (IMMUTABLE)

| Quartile | Historical value |
|---|---|
| Q25 | `0.0001499766777599` |
| Q50 | `0.00033976472454305` |
| Q75 | `0.0008266496069636999` |

Source: `phase4_v2` TRAIN FULL_FIELD, 1,162 components. **Not modified.**

The historical quantile method was **reproduced exactly** from
`reports/tables/kub_train_components_sized.csv` (SHA `da31c7d7…`, matching the frozen
provenance) before being applied to clean-v3.

## 3. Freeze sequencing (enforced)

1. derive clean-v3 quartiles from **TRAIN only**
2. persist `reports/audits/kub_size_clean_v3_v1_thresholds.json`
3. hash it — SHA `895cd9d60f7ac5701b6800b751f157a54387bd9828da99da8982d9dc70047922`
4. mark **FROZEN**
5. **only then** read VAL medical content
6. apply the frozen thresholds unchanged

**VAL content reads before freeze: 0.** Thresholds changed after VAL: **NO**.

## 4. Frozen distributions

| Stratum | TRAIN objects | TRAIN % | VAL objects | VAL % |
|---|---:|---:|---:|---:|
| TINY | 291 | 25.06 | 72 | 47.37 |
| SMALL | 290 | 24.98 | 28 | 18.42 |
| MEDIUM | 290 | 24.98 | 36 | 23.68 |
| LARGE | 290 | 24.98 | 16 | 10.53 |

TRAIN is quartile-balanced **by construction**. VAL is **not** balanced — this reflects
VAL composition and is **not** a reason to move the thresholds.

VAL population: 103 FULL_FIELD cases / 152 objects.

## 5. TRAIN historical-vs-clean crosswalk

2 of 1,161 objects (0.1723%) change stratum between `kub_size_v1` and
`kub_size_clean_v3_v1`. Descriptive only — the clean thresholds were **not** adjusted
based on this comparison.

Precision note: the canonical thresholds are the exact float64 quartiles. The
persisted-table variant differs by ≤2.4e-13 relative and changes 3 objects'
classification — an immaterial boundary-sensitivity effect, reported for transparency.

## 6. Corrections recorded in Part 1B

The Part-1A recommendation JSON contained stale wording calling C2 "the only candidate
meaningfully comparable across both regimes", which contradicted Part-1A's own evidence.
**Corrected here:** C2 is **scale-normalized but NOT cross-regime calibrated** (a
FULL_FIELD-calibrated C2 rule sends ~99.5% of ROI components to LARGE). This is one
reason it was not selected. **The accepted Part-1A notebook was not modified.**

## 7. Downstream governance

- All CLEAN-v3 KUB work must use `taxonomy_id = kub_size_clean_v3_v1`.
- Historical v2 reports retain `kub_size_v1`.
- Do **not** compare historical and clean size labels as if thresholds were identical.
- Any result table containing size strata must record `manifest_version` **and** `taxonomy_id`.
- Case-level fields (`contains_*_object`, `dominant_object_stratum`) are **derived
  convenience metadata**, not the primary taxonomy.
- No ROI-specific taxonomy exists; it would require separate authorization.

## 8. Deliverables
- **Part 1A notebook:** `phase07_tiny_object_definition_train_only_design.ipynb`
- **Part 1B notebook:** `phase07_tiny_object_taxonomy_freeze_clean_v3.ipynb`
- **Modules:** `code/phase07_tiny_definition.py`, `code/phase07b_taxonomy_freeze.py`
- **Extended canonical infra:** `src/analysis/kub_object_size.py` (versioned registry;
  `kub_size_v1` behaviour unchanged)
- **Threshold artifact:** `reports/audits/kub_size_clean_v3_v1_thresholds.json` / `.md`
- **Freeze audit:** `reports/audits/phase07_clean_v3_taxonomy_freeze_audit.json` / `.md`
- **Tables:** `reports/tables/phase07_*.csv`
- **Figures:** `reports/figures/phase07_tiny_object_definition/*.png`
- **Tests:** `tests/test_phase07_taxonomy.py` (22 tests)

## 9. Limitations
- "Tiny" is a **relative, TRAIN-derived geometric stratum**, not an absolute clinical definition.
- The taxonomy applies primarily to **FULL_FIELD** acquisition; ROI is deliberately not binned.
- Thresholds depend on the clean-v3 TRAIN distribution; TRAIN is quartile-balanced by construction.
- VAL prevalence may differ because VAL composition differs.
- VAL was inspected only **after** the threshold freeze; no TEST content was accessed.
- No external literature was consulted.

## 10. Next Phase
- **Phase 08** — NOT STARTED. Awaiting supervisor authorization.

---

# Part 1A — Historical audit + candidate design (candidates NOT frozen)

## A1. Historical definition — `kub_size_v1` (reconstructed, not assumed)

| Field | Value |
|---|---|
| Metric | `component_ratio` = `component_pixels / (native_h × native_w)` |
| Unit | **object** (connected foreground component) |
| Connectivity | **8** |
| Coordinate system | native pixels, **normalized by native image area** |
| Resize convention | none (native); training pipeline separately does aspect-preserving resize + centre pad to 512 |
| Acquisition scope | **FULL_FIELD only** (ROI → `ROI_NOT_PRIMARY_BINNED`) |
| Source | TRAIN only, `phase4_v2`, 1,162 FULL_FIELD components |
| Boundary semantics | lower-inclusive cumulative |

**Critical finding:** the historical metric is connected-component area normalized by
native image area. The "<32 px = tiny" hypothesis is **NOT supported** by any canonical
project source.

**No disagreements** were found between sources (module, threshold record, provenance
record, threshold table, legacy driver, notebook all implement the same taxonomy).

## A2. Unit of Analysis
Both representations are retained:
- **object-level** → `phase07_kub_v3_train_object_geometry.csv`
- **case-level** → `phase07_kub_v3_train_case_size_summary.csv`

Multi-component masks are **not** collapsed. Phase 07 uses **8-connectivity** to match the
historical taxonomy; Phase 06 used scipy's default **4-connectivity**, which is why the
multi-component case count is 210 here vs 212 there.

## A3. CLEAN-v3 TRAIN Population

| Quantity | Value |
|---|---:|
| KUB TRAIN cases | 1978 |
| TRAIN patients | 318 |
| TRAIN objects | 2375 |
| FULL_FIELD objects / cases | 1161 / 770 |
| ROI objects / cases | 1214 / 1208 |
| Multi-component cases (8-conn) | 210 |

## A4. Candidate Taxonomies (EXPLORATORY — superseded by Part 1B)

All cut points derived from **TRAIN FULL_FIELD objects only** (n = 1,161). No VAL data used.

| Candidate | Metric | Unit | Acquisition | T1 | T2 | T3 |
|---|---|---|---|---|---|---|
| **C1** `HISTORICAL_kub_size_v1` | `component_ratio` | object | FULL_FIELD only | `0.0001499766777599` | `0.00033976472454305` | `0.0008266496069636999` |
| **C2** `NORMALIZED_EQ_DIAMETER` | `eq_diameter / min(W,H)` | object | FULL_FIELD-calibrated | `0.01554130` | `0.02307019` | `0.03630086` |
| **C3** `FULLFIELD_NATIVE_EQ_DIAMETER_PX` | `eq_diameter` (px) | object | FULL_FIELD only | `38.0650` | `55.5548` | `85.9940` |

### Critical cross-regime caveat

Applying a **FULL_FIELD-calibrated** rule to ROI crops is **not** valid: an ROI crop
magnifies its object. On `ALL_TRAIN`, C2 pushes **1,498 of 2,375** objects into LARGE —
almost all ROI objects. This **weakens the naive reading of Option B** and strengthens
Options A (FULL_FIELD-scoped) and C (separate per-regime calibration).

## A5. Part-1A recommendation (superseded)

`RECOMMENDED_FOR_SUPERVISOR_REVIEW` → C1 (historical `kub_size_v1`). The supervisor
subsequently authorized the design, and Part 1B froze it as `kub_size_clean_v3_v1` with
quartiles re-derived from CLEAN-v3 TRAIN.

